import React from 'react'
import { Loader2, AlertCircle } from 'lucide-react'

export function Loading({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 py-8 justify-center">
      <Loader2 className="animate-spin" size={18} />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm mb-4">
      <AlertCircle size={18} className="shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  )
}

const STATUS_STYLES = {
  Applied: 'bg-slate-100 text-slate-700',
  Shortlisted: 'bg-amber-100 text-amber-700',
  Selected: 'bg-green-100 text-green-700',
  Rejected: 'bg-red-100 text-red-700',
}

export function StatusBadge({ status }) {
  return <span className={`badge ${STATUS_STYLES[status] || 'bg-slate-100 text-slate-700'}`}>{status}</span>
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-slate-500 text-sm mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function StatCard({ label, value, sub }) {
  return (
    <div className="card">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="text-2xl font-semibold text-slate-900 mt-1">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}
