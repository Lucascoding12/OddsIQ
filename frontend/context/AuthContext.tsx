"use client"

import { createContext, useContext, useSyncExternalStore, ReactNode } from "react"

type User = { email: string } | null

type AuthContextValue = {
  isLoggedIn: boolean
  /** False during SSR/hydration, true once the client store is readable. */
  ready: boolean
  user: User
  login: (email: string) => void
  logout: () => void
}

const STORAGE_KEY = "oddsiq_user"

// localStorage as an external store: snapshot is cached by raw string so
// repeated reads return a stable reference, and login/logout notify
// subscribers (plus the `storage` event for cross-tab sync).
const listeners = new Set<() => void>()
let cachedRaw: string | null = null
let cachedUser: User = null

function getSnapshot(): User {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (raw !== cachedRaw) {
    cachedRaw = raw
    try {
      cachedUser = raw ? (JSON.parse(raw) as User) : null
    } catch {
      cachedUser = null
    }
  }
  return cachedUser
}

function subscribe(callback: () => void): () => void {
  listeners.add(callback)
  window.addEventListener("storage", callback)
  return () => {
    listeners.delete(callback)
    window.removeEventListener("storage", callback)
  }
}

function notify() {
  for (const listener of listeners) listener()
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const user = useSyncExternalStore(subscribe, getSnapshot, () => null)
  const ready = useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  )

  function login(email: string) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ email }))
    notify()
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY)
    notify()
  }

  return (
    <AuthContext.Provider value={{ isLoggedIn: !!user, ready, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider")
  return ctx
}
