"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

type LiveGame = {
  id: string
  homeTeam: string
  awayTeam: string
}

type Props = { onSubmit: (alert: { game: string; betType: string; targetOdds: number; book: string }) => void }

const BOOKS = ["Any Book", "DraftKings", "FanDuel", "BetMGM", "Caesars", "Pinnacle"]
const BET_TYPES = ["Home ML", "Away ML", "Home Spread", "Away Spread", "Over", "Under"]

export function AlertForm({ onSubmit }: Props) {
  const [games, setGames] = useState<LiveGame[]>([])
  const [loading, setLoading] = useState(true)
  const [gameId, setGameId] = useState("")
  const [betType, setBetType] = useState("Home ML")
  const [targetOdds, setTargetOdds] = useState("")
  const [book, setBook] = useState("Any Book")

  useEffect(() => {
    async function fetchGames() {
      try {
        const res = await fetch("http://localhost:8000/api/v1/odds")
        if (!res.ok) throw new Error("Failed")
        const data = await res.json()
        const live: LiveGame[] = (data.games ?? []).map((g: { id: string; homeTeam: string; awayTeam: string }) => ({
          id: g.id,
          homeTeam: g.homeTeam,
          awayTeam: g.awayTeam,
        }))
        setGames(live)
        if (live.length > 0) setGameId(live[0].id)
      } catch {
        setGames([])
      } finally {
        setLoading(false)
      }
    }
    fetchGames()
  }, [])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const selected = games.find((g) => g.id === gameId)
    onSubmit({
      game: selected ? `${selected.awayTeam} @ ${selected.homeTeam}` : gameId,
      betType,
      targetOdds: Number(targetOdds),
      book,
    })
    setTargetOdds("")
  }

  const selectClass = "w-full border rounded-md px-3 py-1.5 text-sm bg-background text-foreground border-border"

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-4 space-y-4">
      <h2 className="font-semibold">Create Alert</h2>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading live games...</p>
      ) : games.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No live games available — connect your Odds API key to pull real games.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>Game</Label>
            <select className={selectClass} value={gameId} onChange={(e) => setGameId(e.target.value)}>
              {games.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.awayTeam} @ {g.homeTeam}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label>Bet Type</Label>
            <select className={selectClass} value={betType} onChange={(e) => setBetType(e.target.value)}>
              {BET_TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label>Target Odds</Label>
            <Input type="number" placeholder="-110 or +150" value={targetOdds} onChange={(e) => setTargetOdds(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>Book</Label>
            <select className={selectClass} value={book} onChange={(e) => setBook(e.target.value)}>
              {BOOKS.map((b) => <option key={b}>{b}</option>)}
            </select>
          </div>
        </div>
      )}

      {!loading && games.length > 0 && (
        <Button type="submit">Create Alert</Button>
      )}
    </form>
  )
}
