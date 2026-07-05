import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { Loading, ErrorBanner, PageHeader } from '../components/Common'
import { Plus, Pencil, Trash2, X, Users } from 'lucide-react'

const emptyForm = { name: '', role: '', package_lpa: '', min_cgpa: '', deadline: '', description: '', required_skills: '', eligible_branches: '' }

function toDatetimeLocal(iso) {
  if (!iso) return ''
  return iso.slice(0, 16)
}

export default function AdminCompanies() {
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const [matchPanel, setMatchPanel] = useState(null) // { company, students }

  const load = () => {
    setLoading(true)
    api.get('/companies')
      .then((res) => setCompanies(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load companies.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openCreate = () => {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(true)
  }

  const openEdit = (c) => {
    setForm({
      name: c.name, role: c.role, package_lpa: c.package_lpa, min_cgpa: c.min_cgpa,
      deadline: toDatetimeLocal(c.deadline), description: c.description || '',
      required_skills: c.required_skills.join(', '),
      eligible_branches: c.eligible_branches ? c.eligible_branches.join(', ') : '',
    })
    setEditingId(c.id)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this company posting? This cannot be undone.')) return
    try {
      await api.delete(`/companies/${id}`)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete company.')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    const payload = {
      name: form.name,
      role: form.role,
      package_lpa: parseFloat(form.package_lpa) || 0,
      min_cgpa: parseFloat(form.min_cgpa) || 0,
      deadline: new Date(form.deadline).toISOString(),
      description: form.description,
      required_skills: form.required_skills.split(',').map((s) => s.trim()).filter(Boolean),
      eligible_branches: form.eligible_branches ? form.eligible_branches.split(',').map((s) => s.trim().toUpperCase()).filter(Boolean) : [],
    }
    try {
      if (editingId) {
        await api.put(`/companies/${editingId}`, payload)
      } else {
        await api.post('/companies', payload)
      }
      setShowForm(false)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save company.')
    } finally {
      setSaving(false)
    }
  }

  const viewMatches = async (company) => {
    setMatchPanel({ company, students: null })
    try {
      const res = await api.get(`/eligibility/${company.id}`)
      setMatchPanel({ company, students: res.data })
    } catch (err) {
      setMatchPanel({ company, students: [], error: 'Failed to load eligible students.' })
    }
  }

  return (
    <Layout>
      <PageHeader
        title="Companies"
        subtitle="Manage company job postings and eligibility criteria."
        action={
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Add Company
          </button>
        }
      />
      <ErrorBanner message={error} />

      {loading ? <Loading /> : (
        <div className="grid md:grid-cols-2 gap-4">
          {companies.map((c) => (
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
                {c.required_skills.map((sk) => (
                  <span key={sk} className="badge bg-brand-50 text-brand-700">{sk}</span>
                ))}
              </div>
              {c.eligible_branches && c.eligible_branches.length > 0 && (
                <div className="text-xs text-slate-500 mt-2">
                  <strong>Eligible Branches:</strong> {c.eligible_branches.join(', ')}
                </div>
              )}
              <p className="text-xs text-slate-400 mt-3">Deadline: {new Date(c.deadline).toLocaleString()}</p>
              <div className="flex justify-between items-center mt-4 pt-3 border-t border-slate-100">
                <button onClick={() => viewMatches(c)} className="flex items-center gap-1 text-sm text-brand-600 font-medium">
                  <Users size={15} /> View eligible students
                </button>
                <div>
                  <button onClick={() => openEdit(c)} className="text-slate-500 hover:text-brand-600 mr-3"><Pencil size={16} /></button>
                  <button onClick={() => handleDelete(c.id)} className="text-slate-500 hover:text-red-600"><Trash2 size={16} /></button>
                </div>
              </div>
            </div>
          ))}
          {companies.length === 0 && <p className="text-slate-400 col-span-2 text-center py-6">No companies added yet.</p>}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 relative">
            <button onClick={() => setShowForm(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
              <X size={20} />
            </button>
            <h2 className="font-semibold text-lg mb-4">{editingId ? 'Edit Company' : 'Add Company'}</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">Company Name</label>
                  <input required className="input mt-1" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Job Role</label>
                  <input required className="input mt-1" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">Package (LPA)</label>
                  <input type="number" step="0.1" className="input mt-1" value={form.package_lpa} onChange={(e) => setForm({ ...form, package_lpa: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Min CGPA</label>
                  <input type="number" step="0.01" min="0" max="10" className="input mt-1" value={form.min_cgpa} onChange={(e) => setForm({ ...form, min_cgpa: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Deadline</label>
                  <input required type="datetime-local" className="input mt-1" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Required Skills (comma separated)</label>
                <input className="input mt-1" value={form.required_skills} onChange={(e) => setForm({ ...form, required_skills: e.target.value })} placeholder="python, sql" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Eligible Branches (comma separated, e.g. CSE, IT, ECE)</label>
                <input className="input mt-1" value={form.eligible_branches} onChange={(e) => setForm({ ...form, eligible_branches: e.target.value })} placeholder="CSE, IT, ECE" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Description</label>
                <textarea className="input mt-1" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Saving...' : 'Save'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {matchPanel && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 relative max-h-[80vh] overflow-y-auto">
            <button onClick={() => setMatchPanel(null)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
              <X size={20} />
            </button>
            <h2 className="font-semibold text-lg mb-1">Eligible Students</h2>
            <p className="text-sm text-slate-500 mb-4">{matchPanel.company.name} — {matchPanel.company.role}</p>
            {matchPanel.students === null ? (
              <Loading />
            ) : matchPanel.students.length === 0 ? (
              <p className="text-sm text-slate-400">No eligible students found yet.</p>
            ) : (
              <ul className="space-y-2">
                {matchPanel.students.map((s) => (
                  <li key={s.student_id} className="flex justify-between items-center border border-slate-100 rounded-lg px-3 py-2">
                    <div>
                      <div className="font-medium text-slate-800 text-sm">{s.name}</div>
                      <div className="text-xs text-slate-400">CGPA {s.cgpa} • {s.skill_match_pct}% skill match</div>
                    </div>
                    <span className="badge bg-brand-50 text-brand-700">Score {s.score}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </Layout>
  )
}
