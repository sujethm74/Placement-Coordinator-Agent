import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  LayoutDashboard, Users, Building2, ClipboardList, BarChart3,
  MessageSquare, Trophy, LogOut, GraduationCap,
} from 'lucide-react'

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const adminLinks = [
    { to: '/admin', label: 'Overview', icon: LayoutDashboard },
    { to: '/admin/students', label: 'Students', icon: Users },
    { to: '/admin/companies', label: 'Companies', icon: Building2 },
    { to: '/admin/applications', label: 'Applications', icon: ClipboardList },
    { to: '/admin/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/admin/leaderboard', label: 'Leaderboard', icon: Trophy },
    { to: '/admin/chatbot', label: 'AI Assistant', icon: MessageSquare },
  ]

  const studentLinks = [
    { to: '/student', label: 'My Dashboard', icon: LayoutDashboard },
    { to: '/student/companies', label: 'Companies', icon: Building2 },
    { to: '/student/applications', label: 'My Applications', icon: ClipboardList },
    { to: '/student/leaderboard', label: 'Leaderboard', icon: Trophy },
    { to: '/student/chatbot', label: 'AI Assistant', icon: MessageSquare },
  ]

  const links = user?.role === 'admin' ? adminLinks : studentLinks

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-64 bg-brand-900 text-white flex flex-col shrink-0">
        <div className="flex items-center gap-2 px-5 py-5 border-b border-white/10">
          <GraduationCap size={26} />
          <div>
            <div className="font-semibold leading-tight">Placement</div>
            <div className="text-xs text-white/60 leading-tight">Coordinator Agent</div>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/admin' || to === '/student'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive ? 'bg-brand-500 text-white' : 'text-white/70 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-3 py-4 border-t border-white/10">
          <div className="px-3 pb-2 text-xs text-white/50 truncate">{user?.email}</div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-white/70 hover:bg-white/10 hover:text-white transition-colors"
          >
            <LogOut size={18} /> Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">{children}</div>
      </main>
    </div>
  )
}
