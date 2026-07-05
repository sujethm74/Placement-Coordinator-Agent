import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ErrorBanner } from '../components/Common'
import { GraduationCap } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const userInfo = await login(email, password)
      navigate(userInfo.role === 'admin' ? '/admin' : '/student')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-6">
          <div className="bg-brand-500 text-white rounded-xl p-3 mb-3">
            <GraduationCap size={28} />
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Placement Coordinator Agent</h1>
          <p className="text-sm text-slate-500">Sign in to your account</p>
        </div>
        <form onSubmit={handleSubmit} className="card space-y-4">
          <ErrorBanner message={error} />
          <div>
            <label className="text-sm font-medium text-slate-700">Email</label>
            <input type="email" required className="input mt-1" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@college.edu" />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700">Password</label>
            <input type="password" required className="input mt-1" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
          <p className="text-xs text-slate-400 text-center">
            Demo — Admin: admin@placement.edu / admin123
          </p>
        </form>
        <p className="text-sm text-center text-slate-500 mt-4">
          New student? <Link to="/register" className="text-brand-600 font-medium">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
