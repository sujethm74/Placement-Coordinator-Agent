import React, { useState, useRef, useEffect } from 'react'
import Layout from '../components/Layout'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { PageHeader } from '../components/Common'
import { Send, Bot, User } from 'lucide-react'

export default function Chatbot() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)

  const isAdmin = user?.role === 'admin'
  const suggestions = isAdmin
    ? [
        'Which students are eligible for Google?',
        'Show top 5 candidates for Microsoft',
        'How many students have been placed?',
      ]
    : [
        'Where am I lagging?',
        'Am I eligible for Google?',
        'Recommend companies for me',
        'How to prepare for Amazon?',
      ]

  useEffect(() => {
    if (user) {
      const greetText = isAdmin
        ? 'Hi! Ask me things like "Which students are eligible for Google?" or "Show top 5 candidates for Microsoft".'
        : `Hi! I am your AI Placement Counselor. 🎓\n\nI can analyze your profile to see where you are lagging, check eligibility for jobs, or recommend roles.\n\nTry clicking one of the suggestions below to get started!`
      setMessages([{ role: 'bot', text: greetText }])
    }
  }, [user])

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const query = text || input
    if (!query.trim()) return
    setMessages((m) => [...m, { role: 'user', text: query }])
    setInput('')
    setLoading(true)
    try {
      const res = await api.post('/chatbot/query', { query })
      setMessages((m) => [...m, { role: 'bot', text: res.data.answer, data: res.data.data }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'bot', text: 'Something went wrong answering that. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <PageHeader
        title={isAdmin ? 'AI Assistant' : 'Placement AI Counselor'}
        subtitle={isAdmin ? 'Rule-based chatbot backed by live placement data.' : 'Get guidance, check eligibility, and target skill gaps.'}
      />
      <div className="card flex flex-col h-[70vh]">
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role === 'bot' && (
                <div className="bg-brand-500 text-white rounded-full p-1.5 h-fit">
                  <Bot size={14} />
                </div>
              )}
              <div
                className={`max-w-xl rounded-xl px-4 py-2 text-sm ${
                  m.role === 'user' ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-700'
                }`}
              >
                <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
                {m.data && m.data.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {m.data.map((d, j) => (
                      <li key={j} className="text-xs bg-white/70 rounded px-2 py-1 text-slate-700">
                        {d.name} {d.score !== undefined && <>— score {d.score}</>}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {m.role === 'user' && (
                <div className="bg-slate-300 text-slate-700 rounded-full p-1.5 h-fit">
                  <User size={14} />
                </div>
              )}
            </div>
          ))}
          <div ref={scrollRef} />
        </div>
        <div className="flex flex-wrap gap-2 my-3">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-full px-3 py-1 text-slate-600 hover:bg-slate-100 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); send() }} className="flex gap-2 pt-2 border-t border-slate-100">
          <input
            className="input"
            placeholder={isAdmin ? 'Ask about eligibility, stats...' : 'Ask where you are lagging, how to prepare...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit" disabled={loading} className="btn-primary flex items-center gap-1">
            <Send size={16} />
          </button>
        </form>
      </div>
    </Layout>
  )
}
