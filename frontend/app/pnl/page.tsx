"use client"

import { BetLogTable } from "@/components/bets/BetLogTable"
import { BetForm } from "@/components/bets/BetForm"
import { useBets } from "@/context/BetsContext"
import { Bet } from "@/lib/mock-data"

export default function PnLPage() {
  const { bets, addBet } = useBets()

  const settled = bets.filter((b) => b.result !== "pending")
  const totalPnl = settled.reduce((sum, b) => sum + b.pnl, 0)
  const wins = settled.filter((b) => b.result === "win").length
  const winRate = settled.length > 0 ? ((wins / settled.length) * 100).toFixed(1) : "0"
  const avgClv = settled.length > 0 ? (settled.reduce((sum, b) => sum + b.clv, 0) / settled.length).toFixed(1) : "0"

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">PnL Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Track your bets and performance</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total PnL", value: `${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`, color: totalPnl >= 0 ? "text-green-600" : "text-red-500" },
          { label: "Win Rate", value: `${winRate}%`, color: "" },
          { label: "Avg CLV", value: `${Number(avgClv) >= 0 ? "+" : ""}${avgClv}`, color: Number(avgClv) >= 0 ? "text-green-600" : "text-red-500" },
          { label: "Total Bets", value: String(bets.length), color: "" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-lg border px-4 py-3">
            <div className="text-xs text-muted-foreground">{stat.label}</div>
            <div className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      <BetLogTable bets={bets} />
      <BetForm onSubmit={addBet} />
    </div>
  )
}
