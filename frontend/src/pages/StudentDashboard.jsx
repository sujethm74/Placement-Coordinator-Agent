import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api, { API_BASE_URL } from '../api'
import { useAuth } from '../context/AuthContext'
import { Loading, ErrorBanner, PageHeader, StatCard } from '../components/Common'
import { Sparkles } from 'lucide-react'

export default function StudentDashboard() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [activeTab, setActiveTab] = useState('upload') // 'upload' or 'text'
  const [file, setFile] = useState(null)
  const [resumeText, setResumeText] = useState('')
  const [resumeResult, setResumeResult] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    if (!user?.studentId) {
      setLoading(false)
      return
    }
    Promise.all([
      api.get(`/students/${user.studentId}`),
      api.get(`/recommendations/jobs-for-student/${user.studentId}`, { params: { top_n: 5 } }),
    ])
      .then(([profRes, recRes]) => {
        setProfile(profRes.data)
        setRecommendations(recRes.data)
      })
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load your dashboard.'))
      .finally(() => setLoading(false))
  }, [user])

  const analyzeResume = async (e) => {
    e.preventDefault()
    setAnalyzing(true)
    setError('')
    try {
      const formData = new FormData()
      if (activeTab === 'upload') {
        if (!file) {
          setError('Please select a file to upload.')
          setAnalyzing(false)
          return
        }
        formData.append('file', file)
      } else {
        if (!resumeText.trim()) {
          setError('Please paste your resume text.')
          setAnalyzing(false)
          return
        }
        formData.append('resume_text', resumeText)
      }

      const res = await api.post('/resume/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setResumeResult(res.data)
      
      // Reload profile and recommendations so the dashboard instantly updates
      if (user?.studentId) {
        api.get(`/students/${user.studentId}`).then((pRes) => setProfile(pRes.data)).catch(() => {})
        api.get(`/recommendations/jobs-for-student/${user.studentId}`, { params: { top_n: 5 } }).then((rRes) => setRecommendations(rRes.data)).catch(() => {})
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze resume.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <Layout>
      <PageHeader title={`Welcome${profile ? ', ' + profile.name : ''}`} subtitle="Your placement snapshot and recommended opportunities." />
      <ErrorBanner message={error} />
      {loading ? <Loading /> : (
        <div className="space-y-6">
          {profile && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="CGPA" value={profile.cgpa} />
              <StatCard label="Branch" value={profile.branch || '—'} />
              <StatCard label="Skills" value={profile.skills.length} />
              <StatCard label="Past Offers" value={profile.past_offers} />
            </div>
          )}

          <div className="card">
            <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2"><Sparkles size={18} className="text-brand-500" /> Recommended Jobs For You</h2>
            {recommendations.length === 0 ? (
              <p className="text-sm text-slate-400">No recommendations available yet — add more skills to your profile.</p>
            ) : (
              <ul className="space-y-2">
                {recommendations.map((r) => (
                  <li key={r.company_id} className="flex justify-between items-center border border-slate-100 rounded-lg px-3 py-2">
                    <div>
                      <div className="font-medium text-slate-800 text-sm">{r.company_name} — {r.role}</div>
                      <div className="text-xs text-slate-400">₹{r.package_lpa} LPA • {r.skill_match_pct}% skill match</div>
                    </div>
                    <span className="badge bg-brand-50 text-brand-700">Score {r.score}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="card">
            <h2 className="font-semibold text-slate-800 mb-1">Resume Analyzer</h2>
            <p className="text-sm text-slate-500 mb-4">Analyze your resume in any format to extract skills and match corresponding opportunities.</p>
            
            {profile?.resume_link && (
              <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 mb-4 flex items-center justify-between text-sm">
                <span className="text-slate-600 font-medium">Saved Resume:</span>
                <a
                  href={`${API_BASE_URL}${profile.resume_link}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand-600 hover:text-brand-700 font-semibold underline flex items-center gap-1"
                >
                  Download / View Resume
                </a>
              </div>
            )}

            <div className="flex border-b border-slate-200 mb-4">
              <button
                type="button"
                className={`py-2 px-4 text-sm font-medium border-b-2 transition-all ${
                  activeTab === 'upload'
                    ? 'border-brand-500 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
                onClick={() => { setActiveTab('upload'); setResumeResult(null); }}
              >
                Upload File
              </button>
              <button
                type="button"
                className={`py-2 px-4 text-sm font-medium border-b-2 transition-all ${
                  activeTab === 'text'
                    ? 'border-brand-500 text-brand-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
                onClick={() => { setActiveTab('text'); setResumeResult(null); }}
              >
                Paste Text
              </button>
            </div>

            <form onSubmit={analyzeResume} className="space-y-4">
              {activeTab === 'upload' ? (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Upload Resume (PDF, DOCX, TXT, PNG, JPG, JPEG, WEBP)</label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg,.webp"
                    className="input w-full file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
                    onChange={(e) => setFile(e.target.files[0])}
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Paste Resume Text</label>
                  <textarea
                    className="input"
                    rows={5}
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    placeholder="Paste resume text here..."
                  />
                </div>
              )}
              <button
                type="submit"
                disabled={analyzing || (activeTab === 'upload' && !file) || (activeTab === 'text' && !resumeText.trim())}
                className="btn-primary"
              >
                {analyzing ? 'Analyzing...' : 'Analyze Resume'}
              </button>
            </form>

            {resumeResult && (
              <div className="mt-6 space-y-6 border-t border-slate-100 pt-6 animate-fade-in">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium text-slate-700 mb-2">Extracted Skills</div>
                    <div className="flex flex-wrap gap-1">
                      {resumeResult.extracted_skills.length === 0 ? (
                        <span className="text-xs text-slate-400">No skills found.</span>
                      ) : (
                        resumeResult.extracted_skills.map((s) => (
                          <span key={s} className="badge bg-slate-100 text-slate-600 capitalize">{s}</span>
                        ))
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-slate-700 mb-2">Suggested Roles</div>
                    <div className="flex flex-wrap gap-1">
                      {resumeResult.suggested_roles.length === 0 ? (
                        <span className="text-xs text-slate-400">No roles suggested.</span>
                      ) : (
                        resumeResult.suggested_roles.map((r) => (
                          <span key={r} className="badge bg-brand-50 text-brand-700">{r}</span>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-sm font-medium text-slate-700 mb-3">AI Matched Jobs</div>
                  {resumeResult.matched_jobs.length === 0 ? (
                    <p className="text-xs text-slate-400">No matching jobs found in the database.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-slate-500 border-b border-slate-200">
                            <th className="pb-2 pr-4">Company & Role</th>
                            <th className="pb-2 pr-4">Package</th>
                            <th className="pb-2 pr-4">Skill Match %</th>
                            <th className="pb-2 text-right">Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resumeResult.matched_jobs.map((job) => (
                            <tr key={job.company_id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                              <td className="py-2.5 pr-4 font-medium text-slate-800">
                                {job.company_name} <span className="text-xs font-normal text-slate-500">({job.role})</span>
                              </td>
                              <td className="py-2.5 pr-4 text-slate-600">₹{job.package_lpa} LPA</td>
                              <td className="py-2.5 pr-4">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                    <div className="bg-brand-500 h-full" style={{ width: `${job.skill_match_pct}%` }}></div>
                                  </div>
                                  <span className="text-xs font-semibold text-slate-700">{job.skill_match_pct}%</span>
                                </div>
                              </td>
                              <td className="py-2.5 text-right">
                                <span className={`badge ${job.score >= 70 ? 'bg-green-50 text-green-700' : job.score >= 40 ? 'bg-amber-50 text-amber-700' : 'bg-slate-50 text-slate-600'}`}>
                                  {job.score}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </Layout>
  )
}
