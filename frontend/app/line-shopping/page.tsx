"use client"

import { useState, useEffect, useCallback } from "react"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { getOdds, type Game } from "@/lib/api"

function formatOdds(o: number | null | undefined) {
  if (o == null) return "—"
  return o > 0 ? `+${o}` : `${o}`
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
    })
  } catch { return iso }
}

function impliedProb(american: number): number {
  if (american > 0) return 100 / (american + 100)
  return Math.abs(american) / (Math.abs(american) + 100)
}

/** For a game, return all books with their h2h odds */
function extractBookLines(game: Game) {
  const lines: { book: string; homeOdds: number | null; awayOdds: number | null }[] = []
  for (const bm of game.bookmakers ?? []) {
    const h2h = bm.markets?.find((m) => m.key === "h2h")
    if (!h2h) continue
    const outcomes: Record<string, number> = {}
    for (const o of h2h.outcomes) outcomes[o.name] = o.price
    lines.push({
      book: bm.title,
      homeOdds: outcomes[game.homeTeam] ?? null,
      awayOdds: outcomes[game.awayTeam] ?? null,
    })
  }
  // Sort by best home odds descending
  return lines.sort((a, b) => (b.homeOdds ?? -9999) - (a.homeOdds ?? -9999))
}

function ComparePanel({ game }: { game: Game }) {
  const lines = extractBookLines(game)
  if (lines.length === 0) {
    return <div className="text-xs text-muted-foreground px-4 py-3">No bookmaker data available.</div>
  }

  // Find best odds per side
  const bestHome = Math.max(...lines.map((l) => l.homeOdds ?? -9999))
  const bestAway = Math.max(...lines.map((l) => l.awayOdds ?? -9999))

  return (
    <div className="border-t border-border bg-muted/5">
      {/* Column header */}
      <div className="grid grid-cols-[180px_1fr_1fr_80px_80px] px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground border-b border-border/50">
        <span>Book</span>
        <span className="text-center">{game.awayTeam}</span>
        <span className="text-center">{game.homeTeam}</span>
        <span className="text-center">Away Vig</span>
        <span className="text-center">Home Vig</span>
      </div>
      {lines.map((line) => {
        const isHomeBest = line.homeOdds === bestHome
        const isAwayBest = line.awayOdds === bestAway
        const awayVig = line.awayOdds != null ? (impliedProb(line.awayOdds) * 100).toFixed(1) : "—"
        const homeVig = line.homeOdds != null ? (impliedProb(line.homeOdds) * 100).toFixed(1) : "—"

        return (
          <div
            key={line.book}
            className="grid grid-cols-[180px_1fr_1fr_80px_80px] px-4 py-2.5 text-sm border-b border-border/30 last:border-0 hover:bg-muted/20 transition-colors"
          >
            <span className="text-muted-foreground font-medium text-xs self-center">{line.book}</span>
            <span className={`text-center font-mono font-semibold self-center ${isAwayBest ? "text-primary text-base" : "text-muted-foreground"}`}>
              {formatOdds(line.awayOdds)}
              {isAwayBest && <span className="ml-1 text-[10px] font-normal text-primary/60">BEST</span>}
            </span>
            <span className={`text-center font-mono font-semibold self-center ${isHomeBest ? "text-primary text-base" : "text-muted-foreground"}`}>
              {formatOdds(line.homeOdds)}
              {isHomeBest && <span className="ml-1 text-[10px] font-normal text-primary/60">BEST</span>}
            </span>
            <span className="text-center text-xs text-muted-foreground self-center">{awayVig}%</span>
            <span className="text-center text-xs text-muted-foreground self-center">{homeVig}%</span>
          </div>
        )
      })}
      <div className="px-4 py-2 text-[11px] text-muted-foreground bg-muted/10 flex gap-4">
        <span><span className="text-primary font-semibold">Purple</span> = best available line for that side</span>
        <span>Vig = implied probability (lower = less juice taken by book)</span>
      </div>
    </div>
  )
}

function GameRow({ game }: { game: Game }) {
  const [expanded, setExpanded] = useState(false)
  const home = game.bestLine.homeMoneyline
  const away = game.bestLine.awayMoneyline
  const bookCount = game.bookmakers?.length ?? 0

  return (
    <div className="border-b border-border/40 last:border-0">
      <div className="grid grid-cols-[1fr_100px_120px_100px_80px] px-4 py-3 hover:bg-muted/10 transition-colors">
        <div>
          <div className="text-sm font-medium">{game.awayTeam} @ {game.homeTeam}</div>
          <div className="text-[11px] text-muted-foreground mt-0.5">{game.sport} · {formatTime(game.commenceTime)}</div>
        </div>
        <div className="self-center text-xs text-muted-foreground text-center">
          {bookCount} {bookCount === 1 ? "book" : "books"}
        </div>
        <div className="self-center text-center font-mono text-sm space-y-0.5">
          <div className="text-muted-foreground">{formatOdds(away)}</div>
          <div className="text-muted-foreground">{formatOdds(home)}</div>
        </div>
        <div className="self-center text-xs text-muted-foreground text-center truncate">
          {game.bestLine.book || "—"}
        </div>
        <div className="self-center text-right">
          <button
            onClick={() => setExpanded((v) => !v)}
            className={`px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
              expanded
                ? "bg-primary/15 text-primary border-primary/30"
                : "text-muted-foreground border-border hover:text-foreground hover:border-primary/40"
            }`}
          >
            {expanded ? "Close" : "Compare"}
          </button>
        </div>
      </div>
      {expanded && <ComparePanel game={game} />}
    </div>
  )
}

const SPORT_CATEGORIES = [
  "All",
  "American Football", "Basketball", "Baseball", "Hockey",
  "Soccer", "Tennis", "Combat Sports", "Cricket", "Rugby",
  "Golf", "Motorsports", "Esports", "Politics & Specials",
]

export default function LineShoppingPage() {
  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [category, setCategory] = useState("All")
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchGames = useCallback(async () => {
    try {
      const data = await getOdds(category !== "All" ? { category } : undefined)
      setGames(data)
      setLastUpdated(new Date())
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [category])

  useEffect(() => {
    setLoading(true)
    fetchGames()
  }, [fetchGames])

  // Auto-refresh every 30s
  useEffect(() => {
    const t = setInterval(fetchGames, 30_000)
    return () => clearInterval(t)
  }, [fetchGames])

  const filtered = games.filter((g) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      g.homeTeam.toLowerCase().includes(q) ||
      g.awayTeam.toLowerCase().includes(q) ||
      g.sport.toLowerCase().includes(q)
    )
  })

  return (
    <ProtectedRoute>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Line <span className="text-primary">Shopping</span></h1>
            <p className="text-sm text-muted-foreground mt-1">
              Compare odds across all books · click Compare on any game
              {lastUpdated && <span className="ml-2">· {lastUpdated.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}</span>}
            </p>
          </div>
          {!loading && (
            <span className="text-[11px] text-muted-foreground border border-border rounded px-2 py-1 font-mono">
              {filtered.length} GAMES
            </span>
          )}
        </div>

        {/* Filters */}
        <div className="flex gap-3 flex-wrap items-center">
          <input
            type="text"
            placeholder="Search teams…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border border-border rounded-md px-3 py-1.5 text-sm bg-background text-foreground placeholder:text-muted-foreground w-52 focus:outline-none focus:border-primary/50"
          />
          <div className="flex flex-wrap gap-1.5">
            {SPORT_CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  category === cat
                    ? "bg-primary/15 text-primary border border-primary/30"
                    : "text-muted-foreground border border-border hover:text-foreground hover:border-foreground/30"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Column headers */}
        <div className="grid grid-cols-[1fr_100px_120px_100px_80px] px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground border-b border-border">
          <span>Game</span>
          <span className="text-center">Books</span>
          <span className="text-center">Best ML (Away / Home)</span>
          <span className="text-center">Best Book</span>
          <span />
        </div>

        {/* Game list */}
        <div className="rounded-lg border border-border overflow-hidden">
          {loading && (
            <div className="flex items-center justify-center py-20 text-sm text-muted-foreground animate-pulse">
              Loading live games…
            </div>
          )}
          {!loading && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="text-sm font-medium text-muted-foreground">No games found</div>
              <div className="text-xs text-muted-foreground mt-1">
                {games.length === 0
                  ? "Trigger a poll to load live odds."
                  : "Try clearing the search or changing the sport filter."}
              </div>
            </div>
          )}
          {!loading && filtered.map((game) => (
            <GameRow key={game.id} game={game} />
          ))}
        </div>
      </div>
    </ProtectedRoute>
  )
}
