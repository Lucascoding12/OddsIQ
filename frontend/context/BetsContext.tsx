"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"
import { getBets, createBet, deleteBet, type Bet, type BetCreate } from "@/lib/api"

type BetsContextValue = {
  bets: Bet[]
  loading: boolean
  addBet: (bet: BetCreate) => Promise<void>
  removeBet: (id: number) => Promise<void>
  refresh: () => Promise<void>
}

const BetsContext = createContext<BetsContextValue | null>(null)

export function BetsProvider({ children }: { children: ReactNode }) {
  const [bets, setBets] = useState<Bet[]>([])
  const [loading, setLoading] = useState(true)

  async function refresh() {
    try {
      const data = await getBets()
      setBets(data)
    } catch (err) {
      console.error("Failed to load bets:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [])

  async function addBet(data: BetCreate) {
    const newBet = await createBet(data)
    setBets((prev) => [newBet, ...prev])
  }

  async function removeBet(id: number) {
    await deleteBet(id)
    setBets((prev) => prev.filter((b) => b.id !== id))
  }

  return (
    <BetsContext.Provider value={{ bets, loading, addBet, removeBet, refresh }}>
      {children}
    </BetsContext.Provider>
  )
}

export function useBets() {
  const ctx = useContext(BetsContext)
  if (!ctx) throw new Error("useBets must be used inside BetsProvider")
  return ctx
}
