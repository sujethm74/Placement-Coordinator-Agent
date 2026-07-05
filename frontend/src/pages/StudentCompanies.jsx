import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { Loading, ErrorBanner, PageHeader } from '../components/Common'
import { CheckCircle2, X } from 'lucide-react'

export default function StudentCompanies() {
  const { user } = useAuth()
  const [companies, setCompanies] = useState([])
  const [appliedIds, setAppliedIds] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [applyingId, setApplyingId] = useState(null)
  const [gapPanel, setGapPanel] = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get('/companies'),
      user?.studentId ? api.get('/applications', { params: { student_id: user.studentId } }) : Promise.resolve({ data: [] }),
    ])
      .then(([compRes, appRes]) => {
        setCompanies(compRes.data)
        setAppliedIds(new Set(appRes.data.map((a) => a.company_id)))
      })
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load companies.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [user])

  const apply = async (companyId) => {
    setApplyingId(companyId)
    setError('')
    try {
      await api.post('/applications', { student_id: user.studentId, company_id: companyId })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to apply.')
    } finally {
      setApplyingId(null)
    }
  }

  const viewGap = async (company) => {
    setGapPanel({ company, result: null })
    try {
      const res = await api.get(`/skill-gap/${user.studentId}/${company.id}`)
      setGapPanel({ company, result: res.data })
    } catch (err) {
      setGapPanel({ company, result: null, error: 'Failed to load skill gap.' })
    }
  }

  return (
    <Layout>
      <PageHeader title="Companies" subtitle="Browse open roles and apply." />
      <ErrorBanner message={error} />
      {loading ? <Loading /> : (
        <div className="grid md:grid-cols-2 gap-4">
          {companies.map((c) => {
            const applied = appliedIds.has(c.id)
            return (
              <div key={c.id} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-800">{c.name}</h3>
                    <p className="text-sm text-slate-500">{c.role}</p>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-brand-600">₹{c.package_lpa} LPA</div>
                    <div className="text-xs text-slate-400">Min CGPA {c.min_cgpa}</div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1 mt-3">
                  {c.required_skills.map((sk) => <span key={sk} className="badge bg-brand-50 text-brand-700">{sk}</span>)}
                </div>
                {c.eligible_branches && c.eligible_branches.length > 0 && (
                  <div className="text-xs text-slate-500 mt-2">
                    <strong>Eligible Branches:</strong> {c.eligible_branches.join(', ')}
                  </div>
                )}
                <p className="text-xs text-slate-400 mt-3">Deadline: {new Date(c.deadline).toLocaleString()}</p>
                <div className="flex justify-between items-center mt-4 pt-3 border-t border-slate-100">
                  <button onClick={() => viewGap(c)} className="text-sm text-slate-500 underline">Check skill gap</button>
                  {applied ? (
                    <span className="flex items-center gap-1 text-green-600 text-sm font-medium"><CheckCircle2 size={16} /> Applied</span>
                  ) : (
                    <button onClick={() => apply(c.id)} disabled={applyingId === c.id} className="btn-primary text-sm py-1.5">
                      {applyingId === c.id ? 'Applying...' : 'Apply'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
          {companies.length === 0 && <p className="text-slate-400 col-span-2 text-center py-6">No companies available right now.</p>}
        </div>
      )}

      {gapPanel && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 relative">
            <button onClick={() => setGapPanel(null)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
              <X size={20} />
            </button>
            <h2 className="font-semibold text-lg mb-1">Skill Gap</h2>
            <p className="text-sm text-slate-500 mb-4">{gapPanel.company.name} — {gapPanel.company.role}</p>
            {!gapPanel.result ? (
              <Loading />
            ) : (
              <div className="space-y-3">
                <div>
                  <div className="text-sm font-medium text-slate-700 mb-1">Your Skills</div>
                  <div className="flex flex-wrap gap-1">
                    {gapPanel.result.student_skills.map((s) => <span key={s} className="badge bg-slate-100 text-slate-600">{s}</span>)}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-slate-700 mb-1">Missing Skills</div>
                  {gapPanel.result.missing_skills.length === 0 ? (
                    <p className="text-sm text-green-600">You have all required skills! 🎉</p>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {gapPanel.result.missing_skills.map((s) => <span key={s} className="badge bg-red-50 text-red-600">{s}</span>)}
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
