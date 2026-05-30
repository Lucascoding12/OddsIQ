"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Bet } from "@/lib/mock-data"

type Props = { onSubmit: (bet: Omit<Bet, "id" | "closingOdds" | "clv">) => void }

function calcPnl(odds: number, stake: number, result: "win" | "loss" | "pending"): number {
  if (result === "pending") return 0
  if (result === "loss") return -stake
  return odds > 0 ? (stake * odds) / 100 : (stake * 100) / Math.abs(odds)
}

const SPORTS = ["NFL", "NBA", "MLB", "NHL"]

export function BetForm({ onSubmit }: Props) {
  const [form, setForm] = useState({ date: "", sport: "NFL", game: "", betType: "", odds: "", stake: "", result: "win" as "win" | "loss" })

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const odds = Number(form.odds)
    const stake = Number(form.stake)
    const pnl = calcPnl(odds, stake, form.result)
    onSubmit({ date: form.date, sport: form.sport, game: form.game, betType: form.betType, odds, stake, result: form.result, pnl })
    setForm({ date: "", sport: "NFL", game: "", betType: "", odds: "", stake: "", result: "win" as "win" | "loss" })
  }

  const previewPnl = form.odds && form.stake ? calcPnl(Number(form.odds), Number(form.stake), form.result) : null

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
          <select className="w-full border rounded-md px-3 py-1.5 text-sm bg-background text-foreground" value={form.sport} onChange={(e) => set("sport", e.target.value)}>
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

      <div className="flex items-center gap-6">
        <div className="flex gap-3">
          {(["win", "loss"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setForm((p) => ({ ...p, result: r }))}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors capitalize ${
                form.result === r
                  ? "border-foreground text-foreground"
                  : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/50"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {previewPnl !== null && (
          <span className="text-sm font-medium font-mono text-muted-foreground">
            {previewPnl >= 0 ? "+" : ""}${previewPnl.toFixed(2)} PnL
          </span>
        )}
      </div>

      <Button type="submit">Log Bet</Button>
    </form>
  )
}
