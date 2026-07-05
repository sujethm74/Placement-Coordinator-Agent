import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { Loading, ErrorBanner, PageHeader, StatCard } from '../components/Common'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'

const COLORS = ['#3366ff', '#93b4ff', '#22c55e', '#f59e0b', '#ef4444']

export default function AdminAnalytics() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/dashboard')
      .then((res) => setStats(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load analytics.'))
      .finally(() => setLoading(false))
  }, [])

  const pieData = stats ? [
    { name: 'Placed', value: stats.total_placed_students },
    { name: 'Not Placed', value: Math.max(stats.total_students - stats.total_placed_students, 0) },
  ] : []

  return (
    <Layout>
      <PageHeader title="Analytics" subtitle="Deeper insight into placement outcomes." />
      <ErrorBanner message={error} />
      {loading ? <Loading /> : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Applications" value={stats.total_applications} />
            <StatCard label="Placement Rate" value={`${stats.placement_rate_pct}%`} />
            <StatCard label="Avg. Package" value={`₹${stats.average_package_lpa} LPA`} />
            <StatCard label="Companies Onboarded" value={stats.total_companies} />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="font-semibold text-slate-800 mb-4">Placement Ratio</h2>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90} paddingAngle={3}>
                      {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h2 className="font-semibold text-slate-800 mb-4">Applications per Company</h2>
              <div style={{ width: '100%', height: 260 }}>
                <ResponsiveContainer>
                  <BarChart data={stats.company_wise_hiring} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
                    <YAxis type="category" dataKey="company_name" tick={{ fontSize: 12 }} width={90} />
                    <Tooltip />
                    <Bar dataKey="applied_count" fill="#3366ff" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
