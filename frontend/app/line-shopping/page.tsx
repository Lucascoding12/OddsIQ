"use client"

import { useState } from "react"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useOdds } from "@/lib/hooks"
import { formatOdds, formatGameTime, impliedPct } from "@/lib/format"
import { type Game } from "@/lib/api"

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
  return lines.sort((a, b) => (b.homeOdds ?? -9999) - (a.homeOdds ?? -9999))
}

function priceClass(odds: number | null, best: number, worst: number) {
  if (odds == null) return "text-muted-foreground"
  if (odds === best) return "text-emerald-300"
  if (odds === worst) return "text-red-400"
  return "text-foreground/80"
}

function ComparePanel({ game }: { game: Game }) {
  const lines = extractBookLines(game)
  if (lines.length === 0) {
    return <div className="px-4 py-3 text-xs text-muted-foreground">No bookmaker data available.</div>
  }

  const homeOdds = lines.map((l) => l.homeOdds).filter((o): o is number => o != null)
  const awayOdds = lines.map((l) => l.awayOdds).filter((o): o is number => o != null)
  const bestHome = Math.max(...homeOdds)
  const worstHome = Math.min(...homeOdds)
  const bestAway = Math.max(...awayOdds)
  const worstAway = Math.min(...awayOdds)

  return (
    <div className="border-t border-border bg-muted/5">
      <div className="grid grid-cols-[140px_1fr_1fr_64px] gap-x-2 border-b border-border/50 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground sm:grid-cols-[180px_1fr_1fr_80px]">
        <span>Book</span>
        <span className="text-center">{game.awayTeam}</span>
        <span className="text-center">{game.homeTeam}</span>
        <span className="text-right">Vig</span>
      </div>
      {lines.map((line) => {
        // Vig = total implied probability over 100% across both sides at this book
        const vig =
          line.homeOdds != null && line.awayOdds != null
            ? impliedPct(line.homeOdds) + impliedPct(line.awayOdds) - 100
            : null

        return (
          <div
            key={line.book}
            className="grid grid-cols-[140px_1fr_1fr_64px] items-center gap-x-2 border-b border-border/30 px-4 py-2.5 text-sm transition-colors last:border-0 hover:bg-muted/20 sm:grid-cols-[180px_1fr_1fr_80px]"
          >
            <span className="truncate text-xs font-medium text-muted-foreground">{line.book}</span>
            <div className="text-center">
              <span className={`font-mono font-semibold ${priceClass(line.awayOdds, bestAway, worstAway)}`}>
                {formatOdds(line.awayOdds)}
              </span>
              <div className="text-[10px] text-muted-foreground/60">
                {line.awayOdds != null ? `${impliedPct(line.awayOdds).toFixed(1)}% imp` : ""}
              </div>
            </div>
            <div className="text-center">
              <span className={`font-mono font-semibold ${priceClass(line.homeOdds, bestHome, worstHome)}`}>
                {formatOdds(line.homeOdds)}
              </span>
              <div className="text-[10px] text-muted-foreground/60">
                {line.homeOdds != null ? `${impliedPct(line.homeOdds).toFixed(1)}% imp` : ""}
              </div>
            </div>
            <span className="text-right font-mono text-xs text-muted-foreground">
              {vig != null ? `${vig.toFixed(1)}%` : "—"}
            </span>
          </div>
        )
      })}
      <div className="flex flex-wrap gap-x-4 gap-y-1 bg-muted/10 px-4 py-2 text-[11px] text-muted-foreground">
        <span><span className="font-semibold text-emerald-300">Green</span> = best price</span>
        <span><span className="font-semibold text-red-400">Red</span> = worst price</span>
        <span>Vig = book&apos;s margin on this market (lower is better)</span>
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
      <div className="grid grid-cols-[1fr_120px_88px] items-center px-4 py-3 transition-colors hover:bg-muted/10 sm:grid-cols-[1fr_90px_120px_110px_88px]">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{game.awayTeam} @ {game.homeTeam}</div>
          <div className="mt-0.5 text-[11px] text-muted-foreground">{game.sport} · {formatGameTime(game.commenceTime)}</div>
        </div>
        <div className="hidden text-center text-xs text-muted-foreground sm:block">
          {bookCount} {bookCount === 1 ? "book" : "books"}
        </div>
        <div className="space-y-0.5 text-center font-mono text-sm">
          <div className="font-semibold text-emerald-300">{formatOdds(away)}</div>
          <div className="font-semibold text-emerald-300">{formatOdds(home)}</div>
        </div>
        <div className="hidden truncate text-center text-xs text-muted-foreground sm:block">
          {game.bestLine.book || "—"}
        </div>
        <div className="text-right">
          <button
            onClick={() => setExpanded((v) => !v)}
            className={`rounded border px-3 py-1.5 text-xs font-medium transition-colors ${
              expanded
                ? "border-primary/30 bg-primary/15 text-primary"
                : "border-border text-muted-foreground hover:border-primary/40 hover:text-foreground"
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

function SkeletonRow() {
  return (
    <div className="grid grid-cols-[1fr_120px_88px] items-center border-b border-border/40 px-4 py-3 last:border-0 sm:grid-cols-[1fr_90px_120px_110px_88px]">
      <div className="space-y-1.5">
        <div className="skeleton h-3.5 w-48" />
        <div className="skeleton h-2.5 w-28" />
      </div>
      <div className="hidden justify-center sm:flex"><div className="skeleton h-3 w-12" /></div>
      <div className="flex flex-col items-center gap-1">
        <div className="skeleton h-3.5 w-12" />
        <div className="skeleton h-3.5 w-12" />
      </div>
      <div className="hidden justify-center sm:flex"><div className="skeleton h-3 w-16" /></div>
      <div className="flex justify-end"><div className="skeleton h-7 w-[72px]" /></div>
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
  const [search, setSearch] = useState("")
  const [category, setCategory] = useState("All")

  const { data: games, isLoading } = useOdds(category !== "All" ? { category } : undefined)

  const list = games ?? []
  const showSkeleton = isLoading && list.length === 0

  const filtered = list.filter((g) => {
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
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Line <span className="text-primary">Shopping</span></h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Every book side by side · green is the best price, red is the worst
            </p>
          </div>
          {!showSkeleton && (
            <span className="shrink-0 rounded border border-border px-2 py-1 font-mono text-[11px] text-muted-foreground">
              {filtered.length} GAMES
            </span>
          )}
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="Search teams…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-52 rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none"
          />
          <div className="flex flex-wrap gap-1.5">
            {SPORT_CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                  category === cat
                    ? "border border-primary/30 bg-primary/15 text-primary"
                    : "border border-border text-muted-foreground hover:border-foreground/30 hover:text-foreground"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Game list */}
        <div className="overflow-hidden rounded-lg border border-border">
          <div className="grid grid-cols-[1fr_120px_88px] border-b border-border bg-muted/30 px-4 py-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground sm:grid-cols-[1fr_90px_120px_110px_88px]">
            <span>Game</span>
            <span className="hidden text-center sm:block">Books</span>
            <span className="text-center">Best ML (A/H)</span>
            <span className="hidden text-center sm:block">Best Book</span>
            <span />
          </div>

          {showSkeleton && Array.from({ length: 7 }, (_, i) => <SkeletonRow key={i} />)}

          {!showSkeleton && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="text-sm font-medium text-muted-foreground">No games found</div>
              <div className="mt-1 text-xs text-muted-foreground">
                {list.length === 0
                  ? "Trigger a poll to load live odds."
                  : "Try clearing the search or changing the sport filter."}
              </div>
            </div>
          )}

          {!showSkeleton && filtered.map((game) => <GameRow key={game.id} game={game} />)}
        </div>
      </div>
    </ProtectedRoute>
  )
}
