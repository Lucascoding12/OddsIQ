"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoggedIn) {
      router.replace("/auth/login?next=" + window.location.pathname)
    }
  }, [isLoggedIn, router])

  if (!isLoggedIn) return null

  return <>{children}</>
}
