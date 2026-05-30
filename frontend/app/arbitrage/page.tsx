"use client"

import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useState } from "react"

// ArbCard uses useState internally so the import stays

type ArbLeg = {
  book: string
  odds: number
  impliedProb: number
}

type ArbOpportunity = {
  id: string
  sport: string
  category: string
  homeTeam: string
  awayTeam: string
  commenceTime: string
  betType: string
  legs: ArbLeg[]
  totalImpliedProb: number
  profitPct: number
  detectedAt: string
}

function formatOdds(o: number) {
  return o > 0 ? `+${o}` : `${o}`
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })
  } catch {
    return iso
  }
}

function ArbCard({ opp }: { opp: ArbOpportunity }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="rounded-lg border bg-card overflow-hidden cursor-pointer hover:border-border/80 transition-colors"
      onClick={() => setExpanded((v) => !v)}
    >
      {/* Card face */}
      <div className="p-4 flex items-start justify-between gap-4">
        {/* Left — game info */}
        <div className="min-w-0 space-y-1">
          <div className="text-sm font-semibold truncate">{opp.awayTeam} @ {opp.homeTeam}</div>
          <div className="text-[11px] text-muted-foreground">{opp.category} · {opp.betType}</div>
          <div className="flex flex-wrap gap-2 pt-1">
            {opp.legs.map((leg, i) => (
              <span key={i} className="text-[11px] border border-border rounded px-2 py-0.5 font-mono text-muted-foreground">
                {leg.book} {formatOdds(leg.odds)}
              </span>
            ))}
          </div>
        </div>

        {/* Right — profit badge */}
        <div className="shrink-0 flex flex-col items-end gap-1.5">
          <div className="rounded-md bg-primary/10 border border-primary/20 px-3 py-1.5 text-center">
            <div className="text-lg font-bold font-mono text-primary">+{opp.profitPct.toFixed(3)}%</div>
            <div className="text-[10px] text-primary/60 uppercase tracking-wider">guaranteed</div>
          </div>
          <div className="text-[11px] text-muted-foreground font-mono">
            {(opp.totalImpliedProb * 100).toFixed(3)}% implied
          </div>
        </div>
      </div>

      {/* Expanded stake breakdown */}
      {expanded && (
        <div className="border-t border-border px-4 py-3 space-y-2 bg-muted/10">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground pb-1">
            Stake breakdown — $1,000 example
          </div>
          {opp.legs.map((leg, i) => {
            const dec = leg.odds > 0 ? leg.odds / 100 + 1 : 100 / Math.abs(leg.odds) + 1
            const stake = (1000 * (1 / dec)) / opp.totalImpliedProb
            const payout = stake * dec
            return (
              <div key={i} className="flex items-center justify-between rounded-md border border-border bg-background px-3 py-2.5 text-sm">
                <div className="flex items-center gap-3">
                  <span className="text-[11px] border border-border rounded px-1.5 py-0.5 text-muted-foreground font-mono">
                    Leg {i + 1}
                  </span>
                  <span className="font-medium">{leg.book}</span>
                  <span className="font-mono text-xs text-muted-foreground">{formatOdds(leg.odds)}</span>
                  <span className="text-[11px] text-muted-foreground hidden sm:inline">({(leg.impliedProb * 100).toFixed(2)}%)</span>
                </div>
                <div className="flex items-center gap-6 text-right">
                  <div>
                    <div className="font-mono font-medium">${stake.toFixed(2)}</div>
                    <div className="text-[11px] text-muted-foreground">stake</div>
                  </div>
                  <div>
                    <div className="font-mono text-muted-foreground">${payout.toFixed(2)}</div>
                    <div className="text-[11px] text-muted-foreground">if win</div>
                  </div>
                </div>
              </div>
            )
          })}
          <div className="flex justify-between pt-2 text-xs text-muted-foreground border-t border-border">
            <span>Detected {formatTime(opp.detectedAt)}</span>
            <span className="text-primary font-medium">
              +${(1000 * (1 / opp.totalImpliedProb - 1)).toFixed(2)} on $1,000
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

// Placeholder — will be replaced with real API call once odds poller is wired up
const MOCK_OPPORTUNITIES: ArbOpportunity[] = []

export default function ArbitragePage() {
  const opportunities = MOCK_OPPORTUNITIES

  return (
    <ProtectedRoute>
      <div className="space-y-5">

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Arbitrage <span className="text-primary">Scanner</span></h1>
            <p className="text-sm text-muted-foreground mt-1">
              Auto-detected opportunities across all books · scans every 30s
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground border border-border rounded px-2.5 py-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground" />
              Waiting for data
            </div>
          </div>
        </div>

        <div className="border-b border-border pb-1 flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {opportunities.length} {opportunities.length === 1 ? "opportunity" : "opportunities"} found
          </span>
        </div>

        {/* How it works — shown when no opportunities yet */}
        {opportunities.length === 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Step 1 — Poll</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                The backend fetches live odds from 40+ books every 30 seconds via The Odds API.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Step 2 — Scan</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                For every game and market, it picks the best odds for each outcome across all books and checks if total implied probability is below 100%.
              </p>
            </div>
            <div className="rounded-lg border bg-card p-4 space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Step 3 — Surface</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Opportunities appear here sorted by profit %, with exact stakes pre-calculated. Click any row to expand.
              </p>
            </div>

            <div className="md:col-span-3 rounded-lg border border-dashed border-border flex flex-col items-center justify-center py-16 text-center">
              <div className="text-sm font-medium text-muted-foreground">No opportunities detected</div>
              <div className="text-xs text-muted-foreground mt-1 max-w-sm">
                Connect an Odds API key and start the poller to begin scanning. True arbs are rare — most sessions find 0–3.
              </div>
            </div>
          </div>
        )}

        {/* Opportunity list */}
        {opportunities.length > 0 && (
          <div className="space-y-2">
            {opportunities.map((opp) => (
              <ArbCard key={opp.id} opp={opp} />
            ))}
          </div>
        )}

      </div>
    </ProtectedRoute>
  )
}
