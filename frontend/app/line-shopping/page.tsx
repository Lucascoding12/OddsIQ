"use client"

import { useState } from "react"
import { BookComparison } from "@/components/odds/BookComparison"
import { MOCK_GAMES, MOCK_BOOK_ODDS } from "@/lib/mock-data"

export default function LineShoppingPage() {
  const [selectedGameId, setSelectedGameId] = useState(MOCK_GAMES[0].id)
  const selectedGame = MOCK_GAMES.find((g) => g.id === selectedGameId)!

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Line Shopping</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Compare odds across all books for a single game
        </p>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm font-medium">Select game:</label>
        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-background"
          value={selectedGameId}
          onChange={(e) => setSelectedGameId(e.target.value)}
        >
          {MOCK_GAMES.map((g) => (
            <option key={g.id} value={g.id}>
              [{g.sport}] {g.awayTeam} @ {g.homeTeam}
            </option>
          ))}
        </select>
      </div>

      <div className="text-sm font-medium text-muted-foreground">
        Showing odds for: <span className="text-foreground">{selectedGame.awayTeam} @ {selectedGame.homeTeam}</span>
      </div>

      <BookComparison books={MOCK_BOOK_ODDS} />
    </div>
  )
}
