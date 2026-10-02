"use client"

import { useLineMovement } from "@/lib/hooks"
import { formatOdds, formatGameTime } from "@/lib/format"

export function LineMovementPanel() {
  const { data, isLoading } = useLineMovement(25)
  const lines = data ?? []
  const loading = isLoading && !data

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="font-semibold">Book Disagreement / Line Disparity</div>
        {!loading && (
          <span className="text-[11px] text-muted-foreground font-mono border border-border rounded px-2 py-0.5">
            {lines.length} signals
          </span>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        Games where books have significantly different prices on the same outcome.
        Large gaps indicate sharp money has already moved some books while others lag.
        Steam flag = &gt;8% implied probability gap between best and worst book.
      </p>

      {loading && (
        <div className="text-xs text-muted-foreground animate-pulse py-4 text-center">Loading live signals…</div>
      )}

      {!loading && lines.length === 0 && (
        <div className="text-xs text-muted-foreground text-center py-6 border border-dashed border-border rounded-lg">
          No disparity signals found. Trigger a poll to load live odds.
        </div>
      )}

      <div className="space-y-2">
        {lines.map((line, i) => (
          <div key={i} className="rounded border px-3 py-2.5 text-sm space-y-1.5">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <span className="font-medium truncate">{line.game}</span>
                <span className="text-muted-foreground text-xs ml-2">{line.outcome}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {line.steamFlag && (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">
                    Steam
                  </span>
                )}
                <span className="text-[11px] font-mono text-primary font-semibold">
                  {line.disparityPct.toFixed(1)}% gap
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-3">
                <span>
                  Worst: <span className="text-foreground font-mono">{formatOdds(line.worstOdds)}</span>
                  <span className="ml-1">@ {line.worstBook}</span>
                </span>
                <span className="text-border">→</span>
                <span>
                  Best: <span className="text-primary font-mono font-semibold">{formatOdds(line.bestOdds)}</span>
                  <span className="ml-1">@ {line.bestBook}</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span>{line.bookCount} books</span>
                <span>·</span>
                <span>{formatGameTime(line.commence_time)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
