"use client"

import { createContext, useContext, useState, ReactNode } from "react"
import { Bet, MOCK_BETS } from "@/lib/mock-data"

type BetsContextValue = {
  bets: Bet[]
  addBet: (bet: Omit<Bet, "id" | "pnl" | "closingOdds" | "clv">) => void
  updateBet: (id: string, updates: Partial<Bet>) => void
}

const BetsContext = createContext<BetsContextValue | null>(null)

export function BetsProvider({ children }: { children: ReactNode }) {
  const [bets, setBets] = useState<Bet[]>(MOCK_BETS)

  function addBet(data: Omit<Bet, "id" | "pnl" | "closingOdds" | "clv">) {
    setBets((prev) => [
      { id: String(Date.now()), pnl: 0, closingOdds: data.odds, clv: 0, ...data },
      ...prev,
    ])
  }

  function updateBet(id: string, updates: Partial<Bet>) {
    setBets((prev) => prev.map((b) => (b.id === id ? { ...b, ...updates } : b)))
  }

  return (
    <BetsContext.Provider value={{ bets, addBet, updateBet }}>
      {children}
    </BetsContext.Provider>
  )
}

export function useBets() {
  const ctx = useContext(BetsContext)
  if (!ctx) throw new Error("useBets must be used inside BetsProvider")
  return ctx
}
