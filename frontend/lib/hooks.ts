"use client"

/**
 * SWR-backed data hooks.
 *
 * All live-odds views poll every 30s. SWR dedupes requests across components,
 * keeps previous data while revalidating (no flicker when switching filters),
 * and serves cached data instantly when navigating back to a page.
 */
import useSWR from "swr"
import {
  getOdds,
  getArbOpportunities,
  getLineMovement,
  getAlerts,
  type Game,
  type ArbOpportunity,
  type LineMovementEntry,
  type Alert,
} from "@/lib/api"

const LIVE = {
  refreshInterval: 30_000,
  dedupingInterval: 10_000,
  keepPreviousData: true,
}

export function useOdds(params?: { sport?: string; category?: string }) {
  const sport = params?.sport ?? ""
  const category = params?.category ?? ""
  return useSWR<Game[]>(
    ["odds", sport, category],
    () =>
      getOdds({
        ...(sport ? { sport } : {}),
        ...(category ? { category } : {}),
      }),
    LIVE,
  )
}

export function useArbOpportunities() {
  return useSWR<ArbOpportunity[]>("arb", () => getArbOpportunities(), LIVE)
}

export function useLineMovement(limit = 25) {
  return useSWR<LineMovementEntry[]>(["line-movement", limit], () => getLineMovement(limit), LIVE)
}

export function useAlerts() {
  return useSWR<Alert[]>("alerts", getAlerts, { revalidateOnFocus: false })
}
