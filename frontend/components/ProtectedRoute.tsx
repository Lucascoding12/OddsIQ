"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, ready } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (ready && !isLoggedIn) {
      router.replace("/auth/login?next=" + window.location.pathname)
    }
  }, [ready, isLoggedIn, router])

  if (!ready || !isLoggedIn) return null

  return <>{children}</>
}
