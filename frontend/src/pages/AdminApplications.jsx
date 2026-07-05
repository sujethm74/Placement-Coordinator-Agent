import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { Loading, ErrorBanner, PageHeader, StatusBadge } from '../components/Common'
import { CalendarPlus, X } from 'lucide-react'

const STATUSES = ['Applied', 'Shortlisted', 'Rejected', 'Selected']

export default function AdminApplications() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('')
  const [scheduling, setScheduling] = useState(null)
  const [interviewForm, setInterviewForm] = useState({ scheduled_at: '', mode: 'online', meeting_link: '', notes: '' })
  const [saving, setSaving] = useState(false)

  const load = (statusFilter = '') => {
    setLoading(true)
    api.get('/applications', { params: statusFilter ? { status: statusFilter } : {} })
      .then((res) => setApplications(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load applications.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleFilter = (status) => {
    setFilter(status)
    load(status)
  }

  const updateStatus = async (id, status) => {
    try {
      await api.patch(`/applications/${id}/status`, { status })
      load(filter)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update status.')
    }
  }

  const openSchedule = (app) => {
    setScheduling(app)
    setInterviewForm({ scheduled_at: '', mode: 'online', meeting_link: '', notes: '' })
  }

  const submitSchedule = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await api.post('/interviews', {
        application_id: scheduling.id,
        scheduled_at: new Date(interviewForm.scheduled_at).toISOString(),
        mode: interviewForm.mode,
        meeting_link: interviewForm.meeting_link,
        notes: interviewForm.notes,
      })
      setScheduling(null)
      load(filter)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to schedule interview.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout>
      <PageHeader title="Applications" subtitle="Track student applications and update their status." />
      <ErrorBanner message={error} />

      <div className="flex gap-2 mb-4">
        <button onClick={() => handleFilter('')} className={`badge ${filter === '' ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600'}`}>All</button>
        {STATUSES.map((s) => (
          <button key={s} onClick={() => handleFilter(s)} className={`badge ${filter === s ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600'}`}>{s}</button>
        ))}
      </div>

      {loading ? <Loading /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="pb-2 pr-4">Student</th>
                <th className="pb-2 pr-4">Company</th>
                <th className="pb-2 pr-4">Applied</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4"></th>
              </tr>
            </thead>
            <tbody>
              {applications.map((a) => (
                <tr key={a.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-3 pr-4 font-medium text-slate-800">{a.student_name}</td>
                  <td className="py-3 pr-4 text-slate-600">{a.company_name}</td>
                  <td className="py-3 pr-4 text-slate-500 text-xs">{new Date(a.applied_at).toLocaleDateString()}</td>
                  <td className="py-3 pr-4">
                    <select
                      value={a.status}
                      onChange={(e) => updateStatus(a.id, e.target.value)}
                      className="text-xs border border-slate-200 rounded-md px-2 py-1"
                    >
                      {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="py-3 pr-4 text-right">
                    <button onClick={() => openSchedule(a)} className="flex items-center gap-1 text-brand-600 text-xs font-medium">
                      <CalendarPlus size={14} /> Schedule Interview
                    </button>
                  </td>
                </tr>
              ))}
              {applications.length === 0 && (
                <tr><td colSpan={5} className="py-6 text-center text-slate-400">No applications found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {scheduling && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 relative">
            <button onClick={() => setScheduling(null)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
              <X size={20} />
            </button>
            <h2 className="font-semibold text-lg mb-1">Schedule Interview</h2>
            <p className="text-sm text-slate-500 mb-4">{scheduling.student_name} — {scheduling.company_name}</p>
            <form onSubmit={submitSchedule} className="space-y-3">
              <div>
                <label className="text-sm font-medium text-slate-700">Date & Time</label>
                <input required type="datetime-local" className="input mt-1" value={interviewForm.scheduled_at} onChange={(e) => setInterviewForm({ ...interviewForm, scheduled_at: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Mode</label>
                <select className="input mt-1" value={interviewForm.mode} onChange={(e) => setInterviewForm({ ...interviewForm, mode: e.target.value })}>
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Meeting Link / Venue</label>
                <input className="input mt-1" value={interviewForm.meeting_link} onChange={(e) => setInterviewForm({ ...interviewForm, meeting_link: e.target.value })} />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Notes</label>
                <textarea className="input mt-1" rows={2} value={interviewForm.notes} onChange={(e) => setInterviewForm({ ...interviewForm, notes: e.target.value })} />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setScheduling(null)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Scheduling...' : 'Schedule'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
