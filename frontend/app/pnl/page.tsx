"use client"

import { ProtectedRoute } from "@/components/ProtectedRoute"
import { BetLogTable } from "@/components/bets/BetLogTable"
import { BetForm } from "@/components/bets/BetForm"
import { useBets } from "@/context/BetsContext"
import { type BetCreate } from "@/lib/api"

export default function PnLPage() {
  const { bets, loading, addBet } = useBets()

  const totalPnl = bets.reduce((sum, b) => sum + b.pnl, 0)
  const wins = bets.filter((b) => b.result === "win").length
  const winRate = bets.length > 0 ? ((wins / bets.length) * 100).toFixed(1) : "0"
  const avgClv = bets.length > 0
    ? (bets.reduce((sum, b) => sum + (b.clv ?? 0), 0) / bets.length).toFixed(1)
    : "0"

  async function handleAddBet(bet: BetCreate) {
    await addBet(bet)
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">PnL <span className="text-primary">Dashboard</span></h1>
          <p className="text-sm text-muted-foreground mt-1">Track your bets and performance</p>
        </div>

        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Total PnL", value: `${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`, highlight: true },
            { label: "Win Rate", value: `${winRate}%`, highlight: false },
            { label: "Avg CLV", value: `${Number(avgClv) >= 0 ? "+" : ""}${avgClv}`, highlight: false },
            { label: "Total Bets", value: loading ? "…" : String(bets.length), highlight: false },
          ].map((stat) => (
            <div key={stat.label} className={`rounded-lg border px-4 py-3 ${stat.highlight ? "border-primary/30 bg-primary/5" : ""}`}>
              <div className="text-xs text-muted-foreground">{stat.label}</div>
              <div className={`text-2xl font-bold mt-1 ${stat.highlight ? "text-primary" : ""}`}>{stat.value}</div>
            </div>
          ))}
        </div>

        <BetLogTable bets={bets} />
        <BetForm onSubmit={handleAddBet} />
      </div>
    </ProtectedRoute>
  )
}
