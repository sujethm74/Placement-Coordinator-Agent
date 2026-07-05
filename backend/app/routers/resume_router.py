import os
import io
import json
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload

from .. import schemas, models, auth, scoring
from ..database import get_db

router = APIRouter(prefix="/resume", tags=["Resume Analyzer"])
logger = logging.getLogger("uvicorn.error")

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def call_gemini_api(contents, is_image: bool = False, mime_type: Optional[str] = None, is_pdf: bool = False) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    
    if genai is None:
        raise ValueError("google-generativeai package is not installed.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = (
        "You are an expert resume parser and placement assistant.\n"
        "Analyze the resume content and extract the skills and suggest suitable job roles.\n"
        "Rules:\n"
        f"1. Extract standard engineering/placement skills matching this list if applicable: {scoring.COMMON_SKILLS_KEYWORDS}.\n"
        f"2. Suggest up to 5 suitable job roles from this list: {list(scoring.ROLE_SKILL_MAP.keys())}.\n"
        "3. Return the result strictly in the following JSON format:\n"
        "{\n"
        "  \"extracted_skills\": [\"skill1\", \"skill2\"],\n"
        "  \"suggested_roles\": [\"role1\", \"role2\"]\n"
        "}\n"
    )
    
    if is_image:
        payload = [
            {"mime_type": mime_type or "image/png", "data": contents},
            prompt
        ]
    elif is_pdf:
        payload = [
            {"mime_type": "application/pdf", "data": contents},
            prompt
        ]
    else:
        payload = [prompt, f"Resume Text:\n{contents}"]
        
    response = model.generate_content(
        payload,
        generation_config={"response_mime_type": "application/json"}
    )
    
    try:
        data = json.loads(response.text.strip())
        return {
            "extracted_skills": [str(s).lower() for s in data.get("extracted_skills", [])],
            "suggested_roles": [str(r) for r in data.get("suggested_roles", [])]
        }
    except Exception as e:
        logger.error(f"Failed to parse Gemini JSON: {response.text}, error: {str(e)}")
        raise ValueError("Gemini returned invalid JSON structure")


def extract_text_from_pdf(content: bytes) -> str:
    import pypdf
    pdf_file = io.BytesIO(content)
    try:
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF file: {str(e)}")


def extract_text_from_docx(content: bytes) -> str:
    import docx
    docx_file = io.BytesIO(content)
    try:
        doc = docx.Document(docx_file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Word Document: {str(e)}")


@router.post("/analyze", response_model=schemas.ResumeAnalysis)
async def analyze_resume(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    extracted_text = ""
    skills = []
    roles = []
    
    content_type = request.headers.get("content-type", "")
    
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        resume_text = form.get("resume_text")
        
        if file and hasattr(file, "filename") and file.filename != "":
            content_bytes = await file.read()
            filename = file.filename or ""
            ext = os.path.splitext(filename)[1].lower()
            file_mime = file.content_type or ""
            
            # Save file to uploads if student is logged in
            if current_user.student:
                upload_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"))
                os.makedirs(upload_dir, exist_ok=True)
                safe_filename = f"student_{current_user.student.id}_resume{ext}"
                file_path = os.path.join(upload_dir, safe_filename)
                with open(file_path, "wb") as buffer:
                    buffer.write(content_bytes)
                current_user.student.resume_link = f"/uploads/{safe_filename}"
            
            if ext == ".pdf" or file_mime == "application/pdf":
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    try:
                        result = call_gemini_api(content_bytes, is_pdf=True)
                        skills = result.get("extracted_skills", [])
                        roles = result.get("suggested_roles", [])
                    except Exception as e:
                        logger.error(f"Gemini PDF analysis failed: {str(e)}. Falling back to local PDF parser.")
                        extracted_text = extract_text_from_pdf(content_bytes)
                else:
                    extracted_text = extract_text_from_pdf(content_bytes)
            elif ext in [".docx", ".doc"] or "word" in file_mime:
                extracted_text = extract_text_from_docx(content_bytes)
            elif ext == ".txt" or "text" in file_mime:
                try:
                    extracted_text = content_bytes.decode("utf-8")
                except Exception:
                    extracted_text = content_bytes.decode("latin-1")
            elif ext in [".png", ".jpg", ".jpeg", ".webp"] or file_mime.startswith("image/"):
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise HTTPException(
                        status_code=400,
                        detail="Analyzing resume images requires a GEMINI_API_KEY configured in the environment."
                    )
                try:
                    mime = file_mime if file_mime.startswith("image/") else "image/png"
                    result = call_gemini_api(content_bytes, is_image=True, mime_type=mime)
                    skills = result.get("extracted_skills", [])
                    roles = result.get("suggested_roles", [])
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"AI model error: {str(e)}")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format: {filename}. Supported formats are: pdf, docx, txt, png, jpg, jpeg, webp."
                )
        elif resume_text:
            extracted_text = str(resume_text)
        else:
            raise HTTPException(
                status_code=400,
                detail="Please provide either a resume file upload or paste raw resume text."
            )
    else:
        try:
            body = await request.json()
            extracted_text = body.get("resume_text", "")
            if not extracted_text:
                raise ValueError()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Please provide resume_text in JSON body, or use multipart/form-data upload."
            )
        
    if not skills and not extracted_text:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract any text from the PDF file. "
                "If this is a scanned PDF (image-only), please configure a GEMINI_API_KEY "
                "in the backend environment to enable AI OCR analysis, or copy and paste the resume text directly."
            )
        )

    if extracted_text and not skills:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                result = call_gemini_api(extracted_text)
                skills = result.get("extracted_skills", [])
                roles = result.get("suggested_roles", [])
            except Exception as e:
                logger.error(f"Gemini API analysis failed: {str(e)}. Falling back to rule-based model.")
                skills = scoring.extract_skills_from_text(extracted_text)
                roles = scoring.suggest_roles_from_skills(skills)
        else:
            skills = scoring.extract_skills_from_text(extracted_text)
            roles = scoring.suggest_roles_from_skills(skills)
            
    # Persist the extracted skills and link to DB if it is a student profile
    if current_user.student:
        if skills:
            from ..crud_helpers import set_student_skills
            set_student_skills(db, current_user.student, skills)
        db.commit()
        db.refresh(current_user.student)

    # Calculate matched jobs/companies based on skills
    matched_jobs = []
    companies = db.query(models.Company).options(
        joinedload(models.Company.required_skills).joinedload(models.CompanySkill.skill)
    ).all()
    
    s_skills = {scoring.normalize_skill(s) for s in skills}
    
    # Use real user stats if student is logged in, else default stats
    cgpa = 8.0
    past_offers = 0
    if current_user.student:
        cgpa = current_user.student.cgpa
        past_offers = current_user.student.past_offers
        
    cgpa_norm = min(cgpa / scoring.MAX_CGPA, 1.0) * 100
    past_perf_norm = min(past_offers / scoring.MAX_PAST_OFFERS_CONSIDERED, 1.0) * 100
    
    for c in companies:
        c_skills = scoring.company_skill_set(c)
        match_pct = scoring.skill_match_pct(s_skills, c_skills)
        
        total = (
            (match_pct * scoring.SKILL_WEIGHT)
            + (cgpa_norm * scoring.CGPA_WEIGHT)
            + (past_perf_norm * scoring.PAST_PERFORMANCE_WEIGHT)
        )
        
        matched_jobs.append(schemas.MatchedJob(
            company_id=c.id,
            company_name=c.name,
            role=c.role,
            package_lpa=c.package_lpa,
            skill_match_pct=match_pct,
            score=round(total, 2)
        ))
        
    matched_jobs.sort(key=lambda x: x.score, reverse=True)
    
    return schemas.ResumeAnalysis(
        extracted_skills=skills,
        suggested_roles=roles,
        matched_jobs=matched_jobs
    )
