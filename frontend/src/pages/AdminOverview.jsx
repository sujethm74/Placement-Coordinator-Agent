import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { Loading, ErrorBanner, PageHeader, StatCard } from '../components/Common'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function AdminOverview() {
  const [stats, setStats] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.get('/dashboard'), api.get('/notifications')])
      .then(([dashRes, notifRes]) => {
        setStats(dashRes.data)
        setAlerts(notifRes.data.live_alerts || [])
      })
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load dashboard.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Layout>
      <PageHeader title="Overview" subtitle="Live snapshot of placement activity across the college." />
      <ErrorBanner message={error} />
      {loading ? (
        <Loading />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Students" value={stats.total_students} />
            <StatCard label="Total Companies" value={stats.total_companies} />
            <StatCard label="Students Placed" value={stats.total_placed_students} sub={`${stats.placement_rate_pct}% placement rate`} />
            <StatCard label="Avg. Package" value={`₹${stats.average_package_lpa} LPA`} />
          </div>

          <div className="card">
            <h2 className="font-semibold text-slate-800 mb-4">Company-wise Hiring</h2>
            {stats.company_wise_hiring.length === 0 ? (
              <p className="text-sm text-slate-400">No applications recorded yet.</p>
            ) : (
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={stats.company_wise_hiring}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="company_name" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="applied_count" fill="#93b4ff" name="Applied" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="selected_count" fill="#3366ff" name="Selected" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="card">
            <h2 className="font-semibold text-slate-800 mb-4">Live Alerts</h2>
            {alerts.length === 0 ? (
              <p className="text-sm text-slate-400">No upcoming deadlines or interviews in the next 3 days.</p>
            ) : (
              <ul className="space-y-2">
                {alerts.map((a, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className={`badge ${a.category === 'deadline' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                      {a.category}
                    </span>
                    <span className="text-slate-700">{a.message}</span>
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
