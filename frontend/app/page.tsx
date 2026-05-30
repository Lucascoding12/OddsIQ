"use client"

import { useState } from "react"
import { OddsTable } from "@/components/odds/OddsTable"
import { MOCK_GAMES } from "@/lib/mock-data"
import { Button } from "@/components/ui/button"

const SPORTS = ["All", "NFL", "NBA", "MLB", "NHL"] as const

export default function OddsBoardPage() {
  const [activeSport, setActiveSport] = useState<string>("All")

  const filtered = activeSport === "All"
    ? MOCK_GAMES
    : MOCK_GAMES.filter((g) => g.sport === activeSport)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Odds Board</h1>
          <p className="text-sm text-muted-foreground mt-1">Best available lines across all books</p>
        </div>
        <span className="text-xs text-muted-foreground">Refreshes every 30s</span>
      </div>

      <div className="flex gap-2">
        {SPORTS.map((sport) => (
          <Button
            key={sport}
            variant={activeSport === sport ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveSport(sport)}
          >
            {sport}
          </Button>
        ))}
      </div>

      <OddsTable games={filtered} />
    </div>
  )
}
