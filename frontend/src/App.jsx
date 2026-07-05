import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

import Login from './pages/Login'
import Register from './pages/Register'
import AdminOverview from './pages/AdminOverview'
import AdminStudents from './pages/AdminStudents'
import AdminCompanies from './pages/AdminCompanies'
import AdminApplications from './pages/AdminApplications'
import AdminAnalytics from './pages/AdminAnalytics'
import Chatbot from './pages/Chatbot'
import Leaderboard from './pages/Leaderboard'
import StudentDashboard from './pages/StudentDashboard'
import StudentCompanies from './pages/StudentCompanies'
import StudentApplications from './pages/StudentApplications'

function ProtectedRoute({ children, role }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) {
    return <Navigate to={user.role === 'admin' ? '/admin' : '/student'} replace />
  }
  return children
}

export default function App() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={user.role === 'admin' ? '/admin' : '/student'} replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to={user.role === 'admin' ? '/admin' : '/student'} replace /> : <Register />} />

      {/* Admin routes */}
      <Route path="/admin" element={<ProtectedRoute role="admin"><AdminOverview /></ProtectedRoute>} />
      <Route path="/admin/students" element={<ProtectedRoute role="admin"><AdminStudents /></ProtectedRoute>} />
      <Route path="/admin/companies" element={<ProtectedRoute role="admin"><AdminCompanies /></ProtectedRoute>} />
      <Route path="/admin/applications" element={<ProtectedRoute role="admin"><AdminApplications /></ProtectedRoute>} />
      <Route path="/admin/analytics" element={<ProtectedRoute role="admin"><AdminAnalytics /></ProtectedRoute>} />
      <Route path="/admin/leaderboard" element={<ProtectedRoute role="admin"><Leaderboard /></ProtectedRoute>} />
      <Route path="/admin/chatbot" element={<ProtectedRoute role="admin"><Chatbot /></ProtectedRoute>} />

      {/* Student routes */}
      <Route path="/student" element={<ProtectedRoute role="student"><StudentDashboard /></ProtectedRoute>} />
      <Route path="/student/companies" element={<ProtectedRoute role="student"><StudentCompanies /></ProtectedRoute>} />
      <Route path="/student/applications" element={<ProtectedRoute role="student"><StudentApplications /></ProtectedRoute>} />
      <Route path="/student/leaderboard" element={<ProtectedRoute role="student"><Leaderboard /></ProtectedRoute>} />
      <Route path="/student/chatbot" element={<ProtectedRoute role="student"><Chatbot /></ProtectedRoute>} />

      <Route path="*" element={<Navigate to={user ? (user.role === 'admin' ? '/admin' : '/student') : '/login'} replace />} />
    </Routes>
  )
}
