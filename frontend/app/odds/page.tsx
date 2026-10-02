"use client"

import { useState } from "react"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useOdds } from "@/lib/hooks"
import { formatOdds, formatGameTime, formatClockTime } from "@/lib/format"
import { type Game } from "@/lib/api"

const SPORT_CATEGORIES = [
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

const GRID = "grid grid-cols-[minmax(0,1fr)_76px_76px] sm:grid-cols-[minmax(0,1fr)_90px_88px_88px_130px]"

function GameRow({ game }: { game: Game }) {
  const { homeMoneyline: home, awayMoneyline: away, book } = game.bestLine

  return (
    <div className={`${GRID} items-center border-b border-border/40 px-4 py-3 transition-colors last:border-0 hover:bg-primary/[0.04]`}>
      <div className="min-w-0 pr-3">
        <div className="truncate text-sm font-medium leading-snug">{game.awayTeam}</div>
        <div className="truncate text-sm leading-snug text-muted-foreground">@ {game.homeTeam}</div>
        <div className="mt-1 font-mono text-[11px] text-muted-foreground/70">{formatGameTime(game.commenceTime)}</div>
      </div>
      <div className="hidden self-center sm:block">
        <span className="rounded border border-border/60 px-1.5 py-0.5 text-[11px] text-muted-foreground">
          {game.sport}
        </span>
      </div>
      <div className="self-center text-right font-mono text-sm font-semibold text-emerald-300">
        {formatOdds(away)}
      </div>
      <div className="self-center text-right font-mono text-sm font-semibold text-emerald-300">
        {formatOdds(home)}
      </div>
      <div className="hidden min-w-0 self-center pl-3 text-right sm:block">
        <span className="truncate text-xs text-muted-foreground">{book || "—"}</span>
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground/50">
          {game.bookmakers?.length ?? 0} books
        </div>
      </div>
    </div>
  )
}

function SkeletonRow() {
  return (
    <div className={`${GRID} items-center border-b border-border/40 px-4 py-3 last:border-0`}>
      <div className="space-y-1.5 pr-3">
        <div className="skeleton h-3.5 w-36" />
        <div className="skeleton h-3.5 w-28" />
        <div className="skeleton h-2.5 w-20" />
      </div>
      <div className="hidden sm:block"><div className="skeleton h-4 w-12" /></div>
      <div className="flex justify-end"><div className="skeleton h-4 w-12" /></div>
      <div className="flex justify-end"><div className="skeleton h-4 w-12" /></div>
      <div className="hidden flex-col items-end gap-1 pl-3 sm:flex">
        <div className="skeleton h-3 w-16" />
        <div className="skeleton h-2 w-10" />
      </div>
    </div>
  )
}

export default function OddsBoardPage() {
  const [activeCategory, setActiveCategory] = useState<string>("All")
  const [activeSport, setActiveSport] = useState<string>("All")

  const currentCategory = SPORT_CATEGORIES.find((c) => c.label === activeCategory)

  const { data: games, isLoading, isValidating } = useOdds({
    ...(activeSport !== "All" ? { sport: activeSport } : {}),
    ...(activeSport === "All" && activeCategory !== "All" ? { category: activeCategory } : {}),
  })

  const list = games ?? []
  const showSkeleton = isLoading && list.length === 0

  function handleCategoryClick(label: string) {
    setActiveCategory(label)
    setActiveSport("All")
  }

  const displaySport = activeSport !== "All" ? activeSport : activeCategory !== "All" ? activeCategory : "All Sports"

  const categoryButton = (label: string) =>
    `w-full rounded-md px-3 py-2 text-left text-sm font-medium transition-colors ${
      activeCategory === label
        ? "bg-primary/15 text-foreground"
        : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
    }`

  return (
    <ProtectedRoute>
      <div className="flex min-h-[calc(100vh-7rem)] gap-6">

        {/* Left sidebar — desktop only */}
        <aside className="hidden w-52 shrink-0 space-y-1 md:block">
          <div className="px-2 pb-2 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
            Sports
          </div>
          <button onClick={() => handleCategoryClick("All")} className={categoryButton("All")}>
            All Sports
          </button>
          {SPORT_CATEGORIES.map((cat) => (
            <button key={cat.label} onClick={() => handleCategoryClick(cat.label)} className={categoryButton(cat.label)}>
              {cat.label}
            </button>
          ))}
        </aside>

        {/* Main content */}
        <div className="min-w-0 flex-1 space-y-4">

          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="text-xl font-semibold text-primary">{displaySport}</h1>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Best available moneyline across all books · refreshes every 30s
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <span className="flex items-center gap-1.5 rounded border border-border px-2 py-1 font-mono text-[11px] text-muted-foreground">
                <span className={`h-1.5 w-1.5 rounded-full ${isValidating ? "bg-amber-400" : "live-dot bg-emerald-400"}`} />
                {showSkeleton ? "SYNCING" : `${list.length} GAMES`}
              </span>
            </div>
          </div>

          {/* Mobile category picker */}
          <select
            value={activeCategory}
            onChange={(e) => handleCategoryClick(e.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm md:hidden"
          >
            <option value="All">All Sports</option>
            {SPORT_CATEGORIES.map((cat) => (
              <option key={cat.label} value={cat.label}>{cat.label}</option>
            ))}
          </select>

          {/* League sub-filter */}
          {currentCategory && (
            <div className="flex flex-wrap gap-1.5 border-b border-border pb-3">
              <button
                onClick={() => setActiveSport("All")}
                className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                  activeSport === "All"
                    ? "bg-foreground text-background"
                    : "border border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground"
                }`}
              >
                All leagues
              </button>
              {currentCategory.sports.map((sport) => (
                <button
                  key={sport}
                  onClick={() => setActiveSport(sport)}
                  className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                    activeSport === sport
                      ? "bg-foreground text-background"
                      : "border border-border text-muted-foreground hover:border-foreground/40 hover:text-foreground"
                  }`}
                >
                  {sport}
                </button>
              ))}
            </div>
          )}

          {/* Table */}
          <div className="overflow-hidden rounded-lg border border-border">
            <div className={`${GRID} border-b border-border bg-muted/30 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground`}>
              <span>Matchup</span>
              <span className="hidden sm:block">League</span>
              <span className="text-right">Away ML</span>
              <span className="text-right">Home ML</span>
              <span className="hidden pl-3 text-right sm:block">Best Book</span>
            </div>

            {showSkeleton && Array.from({ length: 8 }, (_, i) => <SkeletonRow key={i} />)}

            {!showSkeleton && list.length === 0 && (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="text-sm font-medium text-muted-foreground">No games available</div>
                <div className="mt-1 max-w-xs text-xs text-muted-foreground">
                  {activeSport !== "All"
                    ? `No ${activeSport} events are currently scheduled.`
                    : activeCategory !== "All"
                    ? `No ${activeCategory} events are currently scheduled.`
                    : "No live odds in cache. Trigger a poll from the API."}
                </div>
              </div>
            )}

            {!showSkeleton && list.map((game) => <GameRow key={game.id} game={game} />)}
          </div>

          {list.length > 0 && (
            <p className="text-right font-mono text-[11px] text-muted-foreground/60">
              prices = best available across books · checked {formatClockTime(new Date())}
            </p>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}
