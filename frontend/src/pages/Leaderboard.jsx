import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { Loading, ErrorBanner, PageHeader } from '../components/Common'
import { Trophy } from 'lucide-react'

const MEDAL_COLORS = ['text-yellow-500', 'text-slate-400', 'text-amber-700']

export default function Leaderboard() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/leaderboard')
      .then((res) => setStudents(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load leaderboard.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Layout>
      <PageHeader title="Leaderboard" subtitle="Ranked by CGPA, breadth of skills, and placement history." />
      <ErrorBanner message={error} />
      {loading ? <Loading /> : (
        <div className="card">
          <ul className="divide-y divide-slate-100">
            {students.map((s, i) => (
              <li key={s.id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 text-center font-semibold text-slate-500">
                    {i < 3 ? <Trophy size={18} className={MEDAL_COLORS[i]} /> : i + 1}
                  </div>
                  <div>
                    <div className="font-medium text-slate-800 text-sm">{s.name}</div>
                    <div className="text-xs text-slate-400">{s.branch || '—'} • CGPA {s.cgpa}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400">{s.past_offers} offer(s)</span>
                  <div className="flex flex-wrap gap-1 max-w-xs justify-end">
                    {s.skills.slice(0, 3).map((sk) => (
                      <span key={sk} className="badge bg-slate-100 text-slate-600">{sk}</span>
                    ))}
                  </div>
                </div>
              </li>
            ))}
            {students.length === 0 && <p className="text-slate-400 text-center py-6">No students yet.</p>}
          </ul>
        </div>
      )}
    </Layout>
  )
}
