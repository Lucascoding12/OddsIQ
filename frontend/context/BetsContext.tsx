"use client"

import { createContext, useContext, ReactNode } from "react"
import useSWR from "swr"
import { getBets, createBet, deleteBet, type Bet, type BetCreate } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"

type BetsContextValue = {
  bets: Bet[]
  loading: boolean
  addBet: (bet: BetCreate) => Promise<void>
  removeBet: (id: number) => Promise<void>
  refresh: () => Promise<void>
}

const BetsContext = createContext<BetsContextValue | null>(null)

export function BetsProvider({ children }: { children: ReactNode }) {
  const { isLoggedIn } = useAuth()

  // Key is null until login — anonymous visitors never hit the bets API.
  const { data, isLoading, mutate } = useSWR<Bet[]>(isLoggedIn ? "bets" : null, getBets, {
    revalidateOnFocus: false,
  })

  const bets = data ?? []

  async function addBet(bet: BetCreate) {
    const created = await createBet(bet)
    await mutate((prev) => [created, ...(prev ?? [])], { revalidate: false })
  }

  async function removeBet(id: number) {
    await deleteBet(id)
    await mutate((prev) => (prev ?? []).filter((b) => b.id !== id), { revalidate: false })
  }

  async function refresh() {
    await mutate()
  }

  return (
    <BetsContext.Provider value={{ bets, loading: isLoading, addBet, removeBet, refresh }}>
      {children}
    </BetsContext.Provider>
  )
}

export function useBets() {
  const ctx = useContext(BetsContext)
  if (!ctx) throw new Error("useBets must be used inside BetsProvider")
  return ctx
}
