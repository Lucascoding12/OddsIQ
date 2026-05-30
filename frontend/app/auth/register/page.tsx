"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function RegisterPage() {
  const [form, setForm] = useState({ email: "", password: "", confirm: "" })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (form.password !== form.confirm) {
      alert("Passwords do not match")
      return
    }
    alert("Auth not yet connected — coming in next phase")
  }

  return (
    <div className="max-w-sm mx-auto mt-16 space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Create your account</h1>
        <p className="text-sm text-muted-foreground mt-1">Free forever</p>
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
        <div className="space-y-1.5">
          <Label>Confirm Password</Label>
          <Input type="password" placeholder="••••••••" value={form.confirm} onChange={(e) => setForm((s) => ({ ...s, confirm: e.target.value }))} required />
        </div>
        <Button type="submit" className="w-full">Create account</Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Already have an account? <Link href="/auth/login" className="text-primary hover:underline">Log in</Link>
      </p>
    </div>
  )
}
