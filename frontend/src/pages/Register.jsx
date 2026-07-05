import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ErrorBanner } from '../components/Common'
import { GraduationCap } from 'lucide-react'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', cgpa: '', branch: '', skills: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        email: form.email,
        password: form.password,
        role: 'student',
        name: form.name,
        cgpa: parseFloat(form.cgpa) || 0,
        branch: form.branch,
        skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
      }
      await register(payload)
      navigate('/student')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-6">
          <div className="bg-brand-500 text-white rounded-xl p-3 mb-3">
            <GraduationCap size={28} />
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Create Student Account</h1>
        </div>
        <form onSubmit={handleSubmit} className="card space-y-4">
          <ErrorBanner message={error} />
          <div>
            <label className="text-sm font-medium text-slate-700">Full name</label>
            <input required className="input mt-1" value={form.name} onChange={update('name')} />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Email</label>
            <input type="email" required className="input mt-1" value={form.email} onChange={update('email')} />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Password</label>
            <input type="password" required className="input mt-1" value={form.password} onChange={update('password')} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-slate-700">CGPA</label>
              <input type="number" step="0.01" min="0" max="10" className="input mt-1" value={form.cgpa} onChange={update('cgpa')} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Branch</label>
              <select required className="input mt-1 bg-white" value={form.branch} onChange={update('branch')}>
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
            <label className="text-sm font-medium text-slate-700">Skills (comma separated)</label>
            <input className="input mt-1" value={form.skills} onChange={update('skills')} placeholder="python, react, sql" />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <p className="text-sm text-center text-slate-500 mt-4">
          Already have an account? <Link to="/login" className="text-brand-600 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
