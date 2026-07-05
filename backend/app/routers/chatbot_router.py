"""
Rule-based AI Chatbot.

No external AI API is used. Instead, the query is parsed with simple
pattern matching to detect an intent (eligibility lookup, top-N candidates,
skill gap, placement stats, etc.) and the relevant entity name (company or
student), then dispatches to the same scoring logic used elsewhere in the
app. This keeps every answer explainable and backed by real DB data.
"""
"""
AI Chatbot and Placement Counselor.

Provides a unified interface for placement analysis. If a student is query, 
it evaluates their profile (CGPA, skills, branch) against job opportunities, 
detecting where they are lagging, detailing required steps, recommending matches,
and providing preparation guidance. 
If an admin queries, it responds with coordinator statistics and student matchmaking.
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, auth, scoring
from ..database import get_db

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])


def _find_company_by_name(db: Session, text: str) -> Optional[models.Company]:
    companies = db.query(models.Company).options(
        joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
    ).all()
    text_lower = text.lower()
    for c in companies:
        if c.name.lower() in text_lower:
            return c
    return None


def _find_student_by_name(db: Session, text: str) -> Optional[models.Student]:
    students = db.query(models.Student).options(
        joinedload(models.Student.skills).joinedload(models.StudentSkill.skill)
    ).all()
    text_lower = text.lower()
    for s in students:
        if s.name.lower() in text_lower:
            return s
    return None


def _extract_top_n(text: str, default: int = 5) -> int:
    match = re.search(r"top\s+(\d+)", text.lower())
    return int(match.group(1)) if match else default


@router.post("/query", response_model=schemas.ChatResponse)
def chatbot_query(payload: schemas.ChatQuery, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    text = payload.query.strip()
    text_lower = text.lower()

    # Detect if user is a student, and load student profile
    student = None
    if current_user.role == models.UserRole.STUDENT:
        student = db.query(models.Student).options(
            joinedload(models.Student.skills).joinedload(models.StudentSkill.skill)
        ).filter(models.Student.user_id == current_user.id).first()

    # --- Student-specific flow ---
    if student:
        # Personal analysis / lagging / improve query
        if any(w in text_lower for w in ["lagging", "improve", "weakness", "missing", "analyze me", "my profile", "guidance", "guide me"]):
            companies = db.query(models.Company).options(
                joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
            ).all()
            
            eligible_list = []
            almost_eligible = []
            major_gap = []
            missing_skills_freq = {}

            for c in companies:
                eligible = scoring.is_eligible(student, c)
                c_skills = scoring.company_skill_set(c)
                s_skills = scoring.student_skill_set(student)
                missing = c_skills - s_skills
                cgpa_gap = max(0.0, c.min_cgpa - student.cgpa)
                
                # Check branch eligibility
                branch_eligible = True
                if c.eligible_branches:
                    allowed = {b.strip().upper() for b in c.eligible_branches.split(",") if b.strip()}
                    branch_eligible = not allowed or (student.branch and student.branch.upper() in allowed)

                if eligible:
                    eligible_list.append(c)
                else:
                    # Collect missing skills
                    for ms in missing:
                        missing_skills_freq[ms] = missing_skills_freq.get(ms, 0) + 1
                    
                    # Heuristics for "almost eligible"
                    if len(missing) <= 2 and cgpa_gap <= 0.5 and branch_eligible:
                        almost_eligible.append((c, missing, cgpa_gap))
                    else:
                        reasons = []
                        if cgpa_gap > 0:
                            reasons.append(f"CGPA gap ({student.cgpa} vs {c.min_cgpa})")
                        if not branch_eligible:
                            reasons.append(f"Branch not eligible (requires: {c.eligible_branches})")
                        if len(missing) > 2:
                            reasons.append(f"Missing {len(missing)} skills ({', '.join(sorted(missing))})")
                        major_gap.append((c, reasons))

            # Build a very rich and friendly counseling response
            ans = f"Hello {student.name}! Here is a detailed analysis of your profile:\n\n"
            ans += f"📊 **Your Profile Summary:**\n"
            ans += f"• **CGPA:** {student.cgpa}/10.0\n"
            ans += f"• **Branch:** {student.branch or 'Not Specified'}\n"
            ans += f"• **Skills:** {', '.join(sorted(scoring.student_skill_set(student))) or 'None yet'}\n\n"

            if eligible_list:
                ans += "✅ **Companies you are currently eligible for:**\n"
                for c in sorted(eligible_list, key=lambda x: x.package_lpa, reverse=True)[:5]:
                    ans += f"• **{c.name}** ({c.role}) — Package: ₹{c.package_lpa} LPA\n"
                if len(eligible_list) > 5:
                    ans += f"• *And {len(eligible_list) - 5} more companies...*\n"
                ans += "\n"
            else:
                ans += "⚠️ **Eligibility Alert:** You are not eligible for any companies yet. Let's work on getting you eligible!\n\n"

            if almost_eligible:
                ans += "🎯 **Companies you can target next (Almost Eligible):**\n"
                for c, missing, cgpa_gap in almost_eligible[:5]:
                    gap_details = []
                    if missing:
                        gap_details.append(f"learn: {', '.join(sorted(missing))}")
                    if cgpa_gap > 0:
                        gap_details.append(f"raise CGPA by {round(cgpa_gap, 2)}")
                    ans += f"• **{c.name}** ({c.role}) — Need to {', '.join(gap_details)}\n"
                ans += "\n"

            if missing_skills_freq:
                sorted_missing = sorted(missing_skills_freq.items(), key=lambda x: x[1], reverse=True)
                ans += "💡 **Recommended Action Plan:**\n"
                ans += "To unlock the highest number of placement options, focus on learning these skills:\n"
                for skill, count in sorted_missing[:3]:
                    ans += f"1. **{skill.title()}** (required by {count} target companies)\n"
                ans += "\nKeep building projects and practicing coding to stand out!"
            else:
                ans += "✨ **Excellent work!** You have all the skills required by the current job postings. Focus on preparing for your interviews!"

            return schemas.ChatResponse(answer=ans)

        # Check eligibility for a specific company
        if "eligible" in text_lower:
            company = _find_company_by_name(db, text)
            if company:
                eligible = scoring.is_eligible(student, company)
                c_skills = scoring.company_skill_set(company)
                s_skills = scoring.student_skill_set(student)
                missing = c_skills - s_skills
                cgpa_gap = max(0.0, company.min_cgpa - student.cgpa)
                
                branch_eligible = True
                if company.eligible_branches:
                    allowed = {b.strip().upper() for b in company.eligible_branches.split(",") if b.strip()}
                    branch_eligible = not allowed or (student.branch and student.branch.upper() in allowed)

                if eligible:
                    score_details = scoring.compute_score(student, company)
                    ans = (
                        f"Yes, you are **eligible** for **{company.name}** ({company.role})! 🎉\n\n"
                        f"• Package: ₹{company.package_lpa} LPA\n"
                        f"• Skill Match: {score_details['skill_match_pct']}%\n"
                        f"• Composite Score: {score_details['score']}/100\n\n"
                        "You meet all CGPA, branch, and skill criteria. We highly recommend submitting your application!"
                    )
                else:
                    ans = f"You are currently **not eligible** for **{company.name}** ({company.role}). Here is why:\n\n"
                    if cgpa_gap > 0:
                        ans += f"• **CGPA Requirement:** Your CGPA is {student.cgpa}, but {company.name} requires at least {company.min_cgpa}.\n"
                    if not branch_eligible:
                        ans += f"• **Branch Restriction:** Your branch is {student.branch}, but {company.name} is only accepting {company.eligible_branches}.\n"
                    if missing:
                        ans += f"• **Missing Skills:** You need to learn: {', '.join(sorted(missing))}.\n"
                    ans += f"\n💡 *Tip: Work on these areas to meet their eligibility criteria before the deadline ({company.deadline.strftime('%b %d, %Y')}).*"
                return schemas.ChatResponse(answer=ans)

        # Recommend companies
        if any(w in text_lower for w in ["recommend", "jobs", "what should i apply", "best match", "suggest"]):
            companies = db.query(models.Company).options(
                joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
            ).all()
            
            scored_jobs = []
            for c in companies:
                score_details = scoring.compute_score(student, c)
                eligible = scoring.is_eligible(student, c)
                scored_jobs.append((c, score_details, eligible))
            
            scored_jobs.sort(key=lambda x: (x[2], x[1]["score"]), reverse=True) # prioritize eligible, then highest score
            
            ans = f"Here are the top job recommendations for you, {student.name}:\n\n"
            for i, (c, details, eligible) in enumerate(scored_jobs[:5]):
                status = "Eligible ✅" if eligible else "Not Eligible ⚠️"
                ans += f"{i+1}. **{c.name}** — {c.role}\n"
                ans += f"   • Package: ₹{c.package_lpa} LPA | Skill Match: {details['skill_match_pct']}%\n"
                ans += f"   • Composite Score: {details['score']}/100 | Status: {status}\n\n"
            ans += "💡 *Tip: Apply to the eligible roles first, and start building skills for the roles with high packages where you are close to qualifying.*"
            return schemas.ChatResponse(answer=ans)

        # How to prepare / Guide for a company
        if any(w in text_lower for w in ["prepare", "how to study", "guide me for", "syllabus"]):
            company = _find_company_by_name(db, text)
            if company:
                req_skills = [cs.skill.name for cs in company.required_skills]
                ans = (
                    f"📚 **Preparation Guide for {company.name} ({company.role}):**\n\n"
                    f"• **Job Description:** {company.description or 'No description provided.'}\n"
                    f"• **Package:** ₹{company.package_lpa} LPA\n"
                    f"• **Minimum CGPA:** {company.min_cgpa}\n"
                    f"• **Required Skills:** {', '.join(req_skills) if req_skills else 'Any programming background'}\n\n"
                    "💡 **Study Plan:**\n"
                )
                if req_skills:
                    ans += f"1. **Master Core Skills:** Dedicate time to learn and build mini-projects using: {', '.join(req_skills)}.\n"
                ans += (
                    "2. **Mock Interviews:** Review standard interview questions for "
                    f"'{company.role}' positions.\n"
                    "3. **Optimize Resume:** Highlight your relevant projects and skills before submitting your application.\n"
                )
                return schemas.ChatResponse(answer=ans)

    # --- Admin and fallback intents ---
    # Intent: eligible students for a company (Admin)
    if "eligible" in text_lower and ("for" in text_lower or "company" in text_lower):
        company = _find_company_by_name(db, text)
        if not company:
            return schemas.ChatResponse(answer="I couldn't find that company. Please check the spelling or add it first.")
        students = db.query(models.Student).options(
            joinedload(models.Student.skills).joinedload(models.StudentSkill.skill)
        ).all()
        eligible = []
        for s in students:
            if scoring.is_eligible(s, company):
                details = scoring.compute_score(s, company)
                eligible.append({"name": s.name, "student_id": s.id, "cgpa": s.cgpa, "score": details["score"]})
        eligible.sort(key=lambda r: r["score"], reverse=True)
        answer = (
            f"{len(eligible)} student(s) are eligible for {company.name} ({company.role})."
            if eligible else f"No students currently meet the eligibility criteria for {company.name}."
        )
        return schemas.ChatResponse(answer=answer, data=eligible)

    # Intent: top-N candidates for a company
    if "top" in text_lower and ("candidate" in text_lower or "student" in text_lower):
        company = _find_company_by_name(db, text)
        top_n = _extract_top_n(text)
        if not company:
            return schemas.ChatResponse(answer="I couldn't find that company. Please check the spelling or add it first.")
        students = db.query(models.Student).options(
            joinedload(models.Student.skills).joinedload(models.StudentSkill.skill)
        ).all()
        ranked = []
        for s in students:
            details = scoring.compute_score(s, company)
            ranked.append({"name": s.name, "student_id": s.id, "cgpa": s.cgpa, "score": details["score"]})
        ranked.sort(key=lambda r: r["score"], reverse=True)
        top = ranked[:top_n]
        answer = f"Here are the top {len(top)} candidates for {company.name} ({company.role})."
        return schemas.ChatResponse(answer=answer, data=top)

    # Intent: skill gap
    if "skill gap" in text_lower or "missing skill" in text_lower:
        company = _find_company_by_name(db, text)
        student = _find_student_by_name(db, text)
        if not company or not student:
            return schemas.ChatResponse(answer="Please mention both a valid student name and a company name for a skill gap check.")
        required = scoring.company_skill_set(company)
        have = scoring.student_skill_set(student)
        missing = sorted(required - have)
        answer = (
            f"{student.name} is missing: {', '.join(missing)} for {company.name}."
            if missing else f"{student.name} already has all the skills required for {company.name}."
        )
        return schemas.ChatResponse(answer=answer, data=missing)

    # Intent: placement stats
    if "how many" in text_lower and ("placed" in text_lower or "selected" in text_lower):
        placed = (
            db.query(models.Application.student_id)
            .filter(models.Application.status == models.ApplicationStatus.SELECTED)
            .distinct()
            .count()
        )
        return schemas.ChatResponse(answer=f"{placed} student(s) have been placed so far.")

    # Greeting / generic help
    if student:
        welcome = (
            f"Hello {student.name}! I am your AI Placement Counselor. 🎓\n\n"
            "I can help you analyze your placement readiness and prepare for target roles. Try asking me:\n"
            "• 'Where am I lagging?' — to get a profile analysis and find areas for improvement.\n"
            "• 'Am I eligible for Google?' — to check if you meet a specific company's requirements.\n"
            "• 'Recommend jobs for me' — to see which openings fit you best.\n"
            "• 'How to prepare for Amazon?' — to get a personalized preparation roadmap."
        )
        return schemas.ChatResponse(answer=welcome)

    return schemas.ChatResponse(
        answer=(
            "I can help with things like: "
            "'Which students are eligible for Infosys?', "
            "'Show top 5 candidates for TCS', "
            "'Skill gap for Ravi at Google', or "
            "'How many students have been placed?'"
        )
    )
