"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MOCK_GAMES } from "@/lib/mock-data"

type Props = { onSubmit: (alert: { game: string; betType: string; targetOdds: number; book: string }) => void }

export function AlertForm({ onSubmit }: Props) {
  const [game, setGame] = useState(MOCK_GAMES[0].id)
  const [betType, setBetType] = useState("Home ML")
  const [targetOdds, setTargetOdds] = useState("")
  const [book, setBook] = useState("any")

  const BOOKS = ["any", "DraftKings", "FanDuel", "BetMGM", "Caesars", "Pinnacle"]
  const BET_TYPES = ["Home ML", "Away ML", "Home Spread", "Away Spread", "Over", "Under"]

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const selected = MOCK_GAMES.find((g) => g.id === game)!
    onSubmit({
      game: `${selected.awayTeam} @ ${selected.homeTeam}`,
      betType,
      targetOdds: Number(targetOdds),
      book,
    })
    setTargetOdds("")
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-4 space-y-4">
      <h2 className="font-semibold">Create Alert</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label>Game</Label>
          <select
            className="w-full border rounded-md px-3 py-1.5 text-sm bg-background"
            value={game}
            onChange={(e) => setGame(e.target.value)}
          >
            {MOCK_GAMES.map((g) => (
              <option key={g.id} value={g.id}>
                {g.awayTeam} @ {g.homeTeam}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Bet Type</Label>
          <select
            className="w-full border rounded-md px-3 py-1.5 text-sm bg-background"
            value={betType}
            onChange={(e) => setBetType(e.target.value)}
          >
            {BET_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Target Odds (e.g. -110 or +150)</Label>
          <Input
            type="number"
            placeholder="-110"
            value={targetOdds}
            onChange={(e) => setTargetOdds(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label>Book</Label>
          <select
            className="w-full border rounded-md px-3 py-1.5 text-sm bg-background"
            value={book}
            onChange={(e) => setBook(e.target.value)}
          >
            {BOOKS.map((b) => <option key={b}>{b}</option>)}
          </select>
        </div>
      </div>
      <Button type="submit">Create Alert</Button>
    </form>
  )
}
