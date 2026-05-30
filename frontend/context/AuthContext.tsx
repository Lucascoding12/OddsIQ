"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"

type AuthContextValue = {
  isLoggedIn: boolean
  user: { email: string } | null
  login: (email: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<{ email: string } | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem("oddsiq_user")
    if (stored) setUser(JSON.parse(stored))
    setReady(true)
  }, [])

  function login(email: string) {
    const u = { email }
    setUser(u)
    localStorage.setItem("oddsiq_user", JSON.stringify(u))
  }

  function logout() {
    setUser(null)
    localStorage.removeItem("oddsiq_user")
  }

  if (!ready) return null

  return (
    <AuthContext.Provider value={{ isLoggedIn: !!user, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider")
  return ctx
}
