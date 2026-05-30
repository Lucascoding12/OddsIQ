"use client"

import { useState } from "react"
import { ProtectedRoute } from "@/components/ProtectedRoute"

const SPORTS = ["All", "NFL", "NBA", "MLB", "NHL"] as const

export default function OddsBoardPage() {
  const [activeSport, setActiveSport] = useState<string>("All")

  return (
    <ProtectedRoute>
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Odds Board</h1>
          <p className="text-sm text-muted-foreground mt-1">Best available lines across all books</p>
        </div>
        <span className="text-xs text-muted-foreground">Refreshes every 30s</span>
      </div>

      <div className="flex gap-1.5">
        {SPORTS.map((sport) => (
          <button
            key={sport}
            onClick={() => setActiveSport(sport)}
            className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
              activeSport === sport
                ? "border-foreground text-foreground"
                : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/50"
            }`}
          >
            {sport}
          </button>
        ))}
      </div>

      <div className="rounded-lg border bg-card">
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-sm font-medium text-foreground">No games available</p>
          <p className="text-xs text-muted-foreground mt-1">Connect an odds API key to start pulling live lines</p>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  )
}
