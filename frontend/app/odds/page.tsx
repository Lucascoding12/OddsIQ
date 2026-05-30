"use client"

import { useState } from "react"
import { ProtectedRoute } from "@/components/ProtectedRoute"

type SportCategory = {
  label: string
  sports: string[]
}

const SPORT_CATEGORIES: SportCategory[] = [
  { label: "American Football", sports: ["NFL", "NFL Preseason", "NCAAF", "CFL", "UFL"] },
  { label: "Basketball", sports: ["NBA", "WNBA", "NCAAB", "NCAAW", "EuroLeague", "NBA Summer League"] },
  { label: "Baseball", sports: ["MLB", "MLB Preseason", "NCAA Baseball", "MiLB", "NPB", "KBO"] },
  { label: "Hockey", sports: ["NHL", "AHL", "SHL", "HockeyAllsvenskan", "Liiga", "Mestis"] },
  { label: "Soccer", sports: ["EPL", "Champions League", "Europa League", "La Liga", "Bundesliga", "Serie A", "Ligue 1", "MLS", "EFL Championship", "Liga MX", "Eredivisie", "Brazilian Serie A", "A-League"] },
  { label: "Tennis", sports: ["ATP Tour", "WTA Tour", "Grand Slams", "Challenger"] },
  { label: "Combat Sports", sports: ["UFC", "MMA", "Boxing"] },
  { label: "Cricket", sports: ["IPL", "Big Bash", "Test Cricket", "International Cricket"] },
  { label: "Rugby", sports: ["NRL", "Rugby Union"] },
  { label: "Golf", sports: ["PGA Tour", "Masters", "US Open Golf", "The Open Championship"] },
  { label: "Motorsports", sports: ["Formula 1"] },
  { label: "Esports", sports: ["Esports"] },
  { label: "Politics & Specials", sports: ["US Politics", "Special Markets"] },
]

export default function OddsBoardPage() {
  const [activeCategory, setActiveCategory] = useState<string>("All")
  const [activeSport, setActiveSport] = useState<string>("All")

  const currentCategory = SPORT_CATEGORIES.find((c) => c.label === activeCategory)

  function handleCategoryClick(label: string) {
    setActiveCategory(label)
    setActiveSport("All")
  }

  const displaySport = activeSport !== "All" ? activeSport : activeCategory !== "All" ? activeCategory : "All Sports"

  return (
    <ProtectedRoute>
      <div className="flex gap-6 min-h-[calc(100vh-7rem)]">

        {/* Left sidebar — category + league nav */}
        <aside className="w-52 shrink-0 space-y-1">
          <div className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground px-2 pb-2">
            Sports
          </div>
          <button
            onClick={() => handleCategoryClick("All")}
            className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeCategory === "All"
                ? "bg-primary/15 text-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            }`}
          >
            All Sports
          </button>
          {SPORT_CATEGORIES.map((cat) => (
            <button
              key={cat.label}
              onClick={() => handleCategoryClick(cat.label)}
              className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeCategory === cat.label
                  ? "bg-primary/15 text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </aside>

        {/* Main content */}
        <div className="flex-1 min-w-0 space-y-4">

          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-semibold text-primary">{displaySport}</h1>
              <p className="text-xs text-muted-foreground mt-0.5">Best available lines across all books · refreshes every 30s</p>
            </div>
            <span className="text-[11px] text-muted-foreground border border-border rounded px-2 py-1 font-mono">
              LIVE
            </span>
          </div>

          {/* League sub-filter (only when a category is active) */}
          {currentCategory && (
            <div className="flex flex-wrap gap-1.5 border-b border-border pb-3">
              <button
                onClick={() => setActiveSport("All")}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  activeSport === "All"
                    ? "bg-foreground text-background"
                    : "text-muted-foreground hover:text-foreground border border-border hover:border-foreground/40"
                }`}
              >
                All leagues
              </button>
              {currentCategory.sports.map((sport) => (
                <button
                  key={sport}
                  onClick={() => setActiveSport(sport)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    activeSport === sport
                      ? "bg-foreground text-background"
                      : "text-muted-foreground hover:text-foreground border border-border hover:border-foreground/40"
                  }`}
                >
                  {sport}
                </button>
              ))}
            </div>
          )}

          {/* Table header */}
          <div className="grid grid-cols-[1fr_80px_120px_120px_120px_100px_80px] text-[11px] font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2 border-b border-border">
            <span>Game</span>
            <span>League</span>
            <span className="text-right">Moneyline</span>
            <span className="text-right">Spread</span>
            <span className="text-right">Total</span>
            <span className="text-right">Best Book</span>
            <span />
          </div>

          {/* Empty state */}
          <div className="flex flex-col items-center justify-center py-24 text-center border border-dashed border-border rounded-lg">
            <div className="text-sm font-medium text-muted-foreground">No games available</div>
            <div className="text-xs text-muted-foreground mt-1 max-w-xs">
              {activeSport !== "All"
                ? `No ${activeSport} events are currently scheduled.`
                : "Connect an Odds API key to start pulling live lines."}
            </div>
          </div>

        </div>
      </div>
    </ProtectedRoute>
  )
}
