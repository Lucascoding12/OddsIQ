"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function LoginPage() {
  const [form, setForm] = useState({ email: "", password: "" })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    alert("Auth not yet connected — coming in next phase")
  }

  return (
    <div className="max-w-sm mx-auto mt-16 space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Log in to OddsIQ</h1>
        <p className="text-sm text-muted-foreground mt-1">Track bets, set alerts, find edges</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border p-6">
        <div className="space-y-1.5">
          <Label>Email</Label>
          <Input type="email" placeholder="you@example.com" value={form.email} onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))} required />
        </div>
        <div className="space-y-1.5">
          <Label>Password</Label>
          <Input type="password" placeholder="••••••••" value={form.password} onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))} required />
        </div>
        <Button type="submit" className="w-full">Log in</Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        No account? <Link href="/auth/register" className="text-primary hover:underline">Sign up</Link>
      </p>
    </div>
  )
}
