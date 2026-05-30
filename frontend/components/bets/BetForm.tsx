"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Bet } from "@/lib/mock-data"

type Props = { onSubmit: (bet: Omit<Bet, "id" | "pnl" | "closingOdds" | "clv">) => void }

export function BetForm({ onSubmit }: Props) {
  const [form, setForm] = useState({ date: "", sport: "NFL", game: "", betType: "", odds: "", stake: "" })
  const SPORTS = ["NFL", "NBA", "MLB", "NHL"]

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({ ...form, odds: Number(form.odds), stake: Number(form.stake), result: "pending" })
    setForm({ date: "", sport: "NFL", game: "", betType: "", odds: "", stake: "" })
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-4 space-y-4">
      <h2 className="font-semibold">Log a Bet</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1.5">
          <Label>Date</Label>
          <Input type="date" value={form.date} onChange={(e) => set("date", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Sport</Label>
          <select className="w-full border rounded-md px-3 py-1.5 text-sm bg-background" value={form.sport} onChange={(e) => set("sport", e.target.value)}>
            {SPORTS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Game</Label>
          <Input placeholder="Chiefs vs Bills" value={form.game} onChange={(e) => set("game", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Bet Type</Label>
          <Input placeholder="Chiefs ML" value={form.betType} onChange={(e) => set("betType", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Odds</Label>
          <Input type="number" placeholder="-110" value={form.odds} onChange={(e) => set("odds", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Stake ($)</Label>
          <Input type="number" placeholder="100" value={form.stake} onChange={(e) => set("stake", e.target.value)} required />
        </div>
      </div>
      <Button type="submit">Log Bet</Button>
    </form>
  )
}
