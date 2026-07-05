import React, { createContext, useContext, useState, useCallback } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('pca_user')
    return stored ? JSON.parse(stored) : null
  })

  const login = useCallback(async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    const userInfo = { userId: data.user_id, role: data.role, studentId: data.student_id, email }
    localStorage.setItem('pca_token', data.access_token)
    localStorage.setItem('pca_user', JSON.stringify(userInfo))
    setUser(userInfo)
    return userInfo
  }, [])

  const register = useCallback(async (payload) => {
    const { data } = await api.post('/auth/register', payload)
    const userInfo = { userId: data.user_id, role: data.role, studentId: data.student_id, email: payload.email }
    localStorage.setItem('pca_token', data.access_token)
    localStorage.setItem('pca_user', JSON.stringify(userInfo))
    setUser(userInfo)
    return userInfo
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('pca_token')
    localStorage.removeItem('pca_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
