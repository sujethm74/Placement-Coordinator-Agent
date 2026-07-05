import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { Loading, ErrorBanner, PageHeader } from '../components/Common'
import { Plus, Pencil, Trash2, X, Search } from 'lucide-react'

const emptyForm = { name: '', email: '', phone: '', cgpa: '', branch: '', resume_link: '', skills: '' }

export default function AdminStudents() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const load = (searchTerm = '') => {
    setLoading(true)
    api.get('/students', { params: searchTerm ? { search: searchTerm } : {} })
      .then((res) => setStudents(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load students.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    load(search)
  }

  const openCreate = () => {
    setForm(emptyForm)
    setEditingId(null)
    setShowForm(true)
  }

  const openEdit = (s) => {
    setForm({
      name: s.name, email: s.email, phone: s.phone || '', cgpa: s.cgpa,
      branch: s.branch || '', resume_link: s.resume_link || '', skills: s.skills.join(', '),
    })
    setEditingId(s.id)
    setShowForm(true)
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this student? This cannot be undone.')) return
    try {
      await api.delete(`/students/${id}`)
      load(search)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete student.')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    const payload = {
      name: form.name,
      email: form.email,
      phone: form.phone,
      cgpa: parseFloat(form.cgpa) || 0,
      branch: form.branch,
      resume_link: form.resume_link,
      skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
    }
    try {
      if (editingId) {
        await api.put(`/students/${editingId}`, payload)
      } else {
        await api.post('/students', payload)
      }
      setShowForm(false)
      load(search)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save student.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout>
      <PageHeader
        title="Students"
        subtitle="Manage student profiles, CGPA and skills."
        action={
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus size={16} /> Add Student
          </button>
        }
      />
      <ErrorBanner message={error} />

      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input className="input pl-9" placeholder="Search by name or email" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <button type="submit" className="btn-secondary">Search</button>
      </form>

      {loading ? <Loading /> : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="pb-2 pr-4">Name</th>
                <th className="pb-2 pr-4">Email</th>
                <th className="pb-2 pr-4">Branch</th>
                <th className="pb-2 pr-4">CGPA</th>
                <th className="pb-2 pr-4">Skills</th>
                <th className="pb-2 pr-4"></th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-3 pr-4 font-medium text-slate-800">{s.name}</td>
                  <td className="py-3 pr-4 text-slate-600">{s.email}</td>
                  <td className="py-3 pr-4 text-slate-600">{s.branch || '—'}</td>
                  <td className="py-3 pr-4 text-slate-600">{s.cgpa}</td>
                  <td className="py-3 pr-4">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {s.skills.slice(0, 4).map((sk) => (
                        <span key={sk} className="badge bg-slate-100 text-slate-600">{sk}</span>
                      ))}
                      {s.skills.length > 4 && <span className="text-xs text-slate-400">+{s.skills.length - 4}</span>}
                    </div>
                  </td>
                  <td className="py-3 pr-4 text-right whitespace-nowrap">
                    <button onClick={() => openEdit(s)} className="text-slate-500 hover:text-brand-600 mr-3"><Pencil size={16} /></button>
                    <button onClick={() => handleDelete(s.id)} className="text-slate-500 hover:text-red-600"><Trash2 size={16} /></button>
                  </td>
                </tr>
              ))}
              {students.length === 0 && (
                <tr><td colSpan={6} className="py-6 text-center text-slate-400">No students found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-lg p-6 relative">
            <button onClick={() => setShowForm(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
              <X size={20} />
            </button>
            <h2 className="font-semibold text-lg mb-4">{editingId ? 'Edit Student' : 'Add Student'}</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">Name</label>
                  <input required className="input mt-1" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Email</label>
                  <input required type="email" className="input mt-1" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">Phone</label>
                  <input className="input mt-1" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">CGPA</label>
                  <input type="number" step="0.01" min="0" max="10" className="input mt-1" value={form.cgpa} onChange={(e) => setForm({ ...form, cgpa: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">Branch</label>
                  <select required className="input mt-1 bg-white" value={form.branch} onChange={(e) => setForm({ ...form, branch: e.target.value })}>
                    <option value="">Select Branch</option>
                    <option value="CSE">CSE</option>
                    <option value="IT">IT</option>
                    <option value="ECE">ECE</option>
                    <option value="EE">EE</option>
                    <option value="ME">ME</option>
                    <option value="CE">CE</option>
                    <option value="MCA">MCA</option>
                    <option value="BCA">BCA</option>
                    <option value="AIDS">AIDS</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Resume Link</label>
                <input className="input mt-1" value={form.resume_link} onChange={(e) => setForm({ ...form, resume_link: e.target.value })} placeholder="https://..." />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Skills (comma separated)</label>
                <input className="input mt-1" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="python, react, sql" />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary">{saving ? 'Saving...' : 'Save'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  )
}
