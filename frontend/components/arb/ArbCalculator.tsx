"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

function americanToDecimal(odds: number): number {
  if (odds > 0) return odds / 100 + 1
  return 100 / Math.abs(odds) + 1
}

function calcArb(leg1Odds: number, leg2Odds: number, totalStake: number) {
  const d1 = americanToDecimal(leg1Odds)
  const d2 = americanToDecimal(leg2Odds)
  const impliedProb = 1 / d1 + 1 / d2
  const isArb = impliedProb < 1
  const stake1 = (totalStake / d1) / impliedProb
  const stake2 = (totalStake / d2) / impliedProb
  const profit = isArb ? totalStake * (1 / impliedProb - 1) : 0
  return { impliedProb, isArb, stake1, stake2, profit }
}

export function ArbCalculator() {
  const [leg1, setLeg1] = useState({ book: "", odds: "" })
  const [leg2, setLeg2] = useState({ book: "", odds: "" })
  const [totalStake, setTotalStake] = useState("1000")
  const [result, setResult] = useState<ReturnType<typeof calcArb> | null>(null)

  function handleCalc(e: React.FormEvent) {
    e.preventDefault()
    setResult(calcArb(Number(leg1.odds), Number(leg2.odds), Number(totalStake)))
  }

  return (
    <form onSubmit={handleCalc} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: "Leg 1", state: leg1, set: setLeg1 },
          { label: "Leg 2", state: leg2, set: setLeg2 },
        ].map(({ label, state, set }) => (
          <div key={label} className="rounded-lg border p-4 space-y-3">
            <div className="font-medium text-sm">{label}</div>
            <div className="space-y-1.5">
              <Label>Book</Label>
              <Input placeholder="e.g. DraftKings" value={state.book} onChange={(e) => set((s) => ({ ...s, book: e.target.value }))} required />
            </div>
            <div className="space-y-1.5">
              <Label>American Odds</Label>
              <Input type="number" placeholder="-110" value={state.odds} onChange={(e) => set((s) => ({ ...s, odds: e.target.value }))} required />
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-end gap-4">
        <div className="space-y-1.5">
          <Label>Total Stake ($)</Label>
          <Input type="number" value={totalStake} onChange={(e) => setTotalStake(e.target.value)} className="w-36" required />
        </div>
        <Button type="submit">Calculate</Button>
      </div>

      {result && (
        <div className={`rounded-lg border p-4 space-y-3 ${result.isArb ? "border-blue-500/40 bg-blue-500/5" : "border-red-500/40 bg-red-500/5"}`}>
          <div className={`font-semibold ${result.isArb ? "text-blue-300" : "text-red-400"}`}>
            {result.isArb ? "Arbitrage Opportunity Found!" : "No Arbitrage — Books are not in your favor"}
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">Implied probability total:</span> <span className="font-medium">{(result.impliedProb * 100).toFixed(2)}%</span></div>
            <div><span className="text-muted-foreground">Guaranteed profit:</span> <span className={`font-medium ${result.isArb ? "text-blue-300" : ""}`}>${result.profit.toFixed(2)}</span></div>
            <div><span className="text-muted-foreground">Stake on Leg 1 ({leg1.book || "Book 1"}):</span> <span className="font-medium">${result.stake1.toFixed(2)}</span></div>
            <div><span className="text-muted-foreground">Stake on Leg 2 ({leg2.book || "Book 2"}):</span> <span className="font-medium">${result.stake2.toFixed(2)}</span></div>
          </div>
        </div>
      )}
    </form>
  )
}
