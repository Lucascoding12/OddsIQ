"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { type AlertCreate } from "@/lib/api"

type Props = { onSubmit: (alert: AlertCreate) => Promise<void> }

const SPORTS = ["NFL", "NBA", "MLB", "NHL", "Tennis", "UFC", "MMA", "Boxing", "NCAAF", "NCAAB", "Soccer"]
const MARKETS = ["h2h", "spreads", "totals"]
const DIRECTIONS = ["above", "below"]

export function AlertForm({ onSubmit }: Props) {
  const [sport, setSport] = useState("NFL")
  const [team, setTeam] = useState("")
  const [market, setMarket] = useState("h2h")
  const [targetOdds, setTargetOdds] = useState("")
  const [direction, setDirection] = useState<"above" | "below">("above")
  const [note, setNote] = useState("")

  const selectClass = "w-full border rounded-md px-3 py-1.5 text-sm bg-background text-foreground border-border"

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    await onSubmit({ sport, team, market, targetOdds: Number(targetOdds), direction, note })
    setTeam("")
    setTargetOdds("")
    setNote("")
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-4 space-y-4">
      <h2 className="font-semibold">Create <span className="text-primary">Alert</span></h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label>Sport</Label>
          <select className={selectClass} value={sport} onChange={(e) => setSport(e.target.value)}>
            {SPORTS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Team / Player</Label>
          <Input placeholder="e.g. Chiefs, Djokovic" value={team} onChange={(e) => setTeam(e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Market</Label>
          <select className={selectClass} value={market} onChange={(e) => setMarket(e.target.value)}>
            {MARKETS.map((m) => <option key={m}>{m}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Target Odds (American)</Label>
          <Input type="number" placeholder="+150 or -110" value={targetOdds} onChange={(e) => setTargetOdds(e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Alert when odds go</Label>
          <select className={selectClass} value={direction} onChange={(e) => setDirection(e.target.value as "above" | "below")}>
            {DIRECTIONS.map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Note (optional)</Label>
          <Input placeholder="e.g. wait for +140 or better" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
      </div>
      <Button type="submit">Create Alert</Button>
    </form>
  )
}
