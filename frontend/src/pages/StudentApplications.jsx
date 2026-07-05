import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { Loading, ErrorBanner, PageHeader, StatusBadge } from '../components/Common'
import { X } from 'lucide-react'

export default function StudentApplications() {
  const { user } = useAuth()
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [withdrawingId, setWithdrawingId] = useState(null)

  const load = () => {
    if (!user?.studentId) {
      setLoading(false)
      return
    }
    setLoading(true)
    api.get('/applications', { params: { student_id: user.studentId } })
      .then((res) => setApplications(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load your applications.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [user])

  const withdraw = async (id) => {
    if (!confirm('Withdraw this application?')) return
    setWithdrawingId(id)
    try {
      await api.delete(`/applications/${id}`)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to withdraw application.')
    } finally {
      setWithdrawingId(null)
    }
  }

  return (
    <Layout>
      <PageHeader title="My Applications" subtitle="Track the status of every company you've applied to." />
      <ErrorBanner message={error} />
      {loading ? <Loading /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="pb-2 pr-4">Company</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Applied On</th>
                <th className="pb-2 pr-4"></th>
              </tr>
            </thead>
            <tbody>
              {applications.map((a) => (
                <tr key={a.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-3 pr-4 font-medium text-slate-800">{a.company_name}</td>
                  <td className="py-3 pr-4"><StatusBadge status={a.status} /></td>
                  <td className="py-3 pr-4 text-slate-500">{new Date(a.applied_at).toLocaleDateString()}</td>
                  <td className="py-3 pr-4 text-right">
                    {a.status === 'Applied' && (
                      <button
                        onClick={() => withdraw(a.id)}
                        disabled={withdrawingId === a.id}
                        className="text-slate-400 hover:text-red-600"
                        title="Withdraw application"
                      >
                        <X size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {applications.length === 0 && (
                <tr><td colSpan={4} className="py-6 text-center text-slate-400">You haven't applied to any companies yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  )
}
