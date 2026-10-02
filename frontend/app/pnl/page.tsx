"use client"

import { ProtectedRoute } from "@/components/ProtectedRoute"
import { BetLogTable } from "@/components/bets/BetLogTable"
import { BetForm } from "@/components/bets/BetForm"
import { PnlSparkline } from "@/components/bets/PnlSparkline"
import { useBets } from "@/context/BetsContext"
import { formatSignedMoney } from "@/lib/format"
import { type BetCreate } from "@/lib/api"

export default function PnLPage() {
  const { bets, loading, addBet } = useBets()

  const settled = bets.filter((b) => b.result !== "pending")
  const totalPnl = bets.reduce((sum, b) => sum + b.pnl, 0)
  const settledStaked = settled.reduce((sum, b) => sum + b.stake, 0)
  const allStaked = bets.reduce((sum, b) => sum + b.stake, 0)
  const roi = settledStaked > 0 ? (totalPnl / settledStaked) * 100 : 0
  const wins = bets.filter((b) => b.result === "win").length
  const losses = bets.filter((b) => b.result === "loss").length
  const pending = bets.length - wins - losses
  const winRate = settled.length > 0 ? (wins / settled.length) * 100 : 0

  async function handleAddBet(bet: BetCreate) {
    await addBet(bet)
  }

  const stats = [
    {
      label: "Total PnL",
      value: formatSignedMoney(totalPnl),
      tone: totalPnl > 0 ? "positive" : totalPnl < 0 ? "negative" : "neutral",
    },
    {
      label: "ROI",
      value: `${roi >= 0 ? "+" : ""}${roi.toFixed(1)}%`,
      tone: roi > 0 ? "positive" : roi < 0 ? "negative" : "neutral",
      hint: "on settled stakes",
    },
    {
      label: "Win Rate",
      value: loading ? "…" : `${winRate.toFixed(1)}%`,
      tone: "neutral",
      hint: `${wins}W – ${losses}L${pending > 0 ? ` – ${pending}P` : ""}`,
    },
    {
      label: "Total Bets",
      value: loading ? "…" : String(bets.length),
      tone: "neutral",
      hint: `$${allStaked.toFixed(0)} staked`,
    },
  ] as const

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">PnL <span className="text-primary">Dashboard</span></h1>
          <p className="mt-1 text-sm text-muted-foreground">Track your bets and performance</p>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className={`rounded-lg border px-4 py-3 ${
                stat.tone === "positive"
                  ? "border-emerald-400/30 bg-emerald-400/5"
                  : stat.tone === "negative"
                  ? "border-red-400/30 bg-red-400/5"
                  : "bg-card"
              }`}
            >
              <div className="text-xs text-muted-foreground">{stat.label}</div>
              <div
                className={`mt-1 font-mono text-2xl font-bold ${
                  stat.tone === "positive" ? "text-emerald-300" : stat.tone === "negative" ? "text-red-400" : ""
                }`}
              >
                {stat.value}
              </div>
              {"hint" in stat && stat.hint && (
                <div className="mt-0.5 text-[11px] text-muted-foreground/70">{stat.hint}</div>
              )}
            </div>
          ))}
        </div>

        <PnlSparkline bets={bets} />

        <BetLogTable bets={bets} loading={loading} />
        <BetForm onSubmit={handleAddBet} />
      </div>
    </ProtectedRoute>
  )
}
