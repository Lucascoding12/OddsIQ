/**
 * Typed API client for the OddsIQ backend.
 * All functions are async and throw on non-2xx responses.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

/** Read the logged-in user's email from localStorage (set by AuthContext). */
function getUserEmail(): string {
  if (typeof window === "undefined") return "anonymous"
  try {
    const stored = localStorage.getItem("oddsiq_user")
    if (stored) return JSON.parse(stored).email ?? "anonymous"
  } catch {}
  return "anonymous"
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-User-Email": getUserEmail(),
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ─── Odds ────────────────────────────────────────────────────────────────────

export type BookmakerOdds = {
  key: string
  title: string
  markets: Array<{
    key: string
    outcomes: Array<{ name: string; price: number }>
  }>
}

export type Game = {
  id: string
  sport: string
  sportKey: string
  category: string
  homeTeam: string
  awayTeam: string
  commenceTime: string
  polledAt?: string
  bestLine: {
    homeMoneyline: number | null
    awayMoneyline: number | null
    book: string
  }
  bookmakers: BookmakerOdds[]
}

export async function getOdds(params?: {
  sport?: string
  sport_key?: string
  category?: string
}): Promise<Game[]> {
  const qs = new URLSearchParams()
  if (params?.sport) qs.set("sport", params.sport)
  if (params?.sport_key) qs.set("sport_key", params.sport_key)
  if (params?.category) qs.set("category", params.category)
  const query = qs.toString() ? `?${qs}` : ""
  return apiFetch<Game[]>(`/api/v1/odds${query}`)
}

export async function getSportCategories(): Promise<Record<string, string[]>> {
  return apiFetch<Record<string, string[]>>("/api/v1/odds/sports")
}

// ─── Arb ─────────────────────────────────────────────────────────────────────

export type ArbLeg = {
  book: string
  outcome: string
  odds: number
  stake: number
  payout: number
}

export type ArbOpportunity = {
  game_id: string
  sport_key: string
  home_team: string
  away_team: string
  commence_time: string
  legs: ArbLeg[]
  profit_pct: number
  total_stake: number
}

export async function getArbOpportunities(params?: {
  sport_key?: string
  min_profit_pct?: number
}): Promise<ArbOpportunity[]> {
  const qs = new URLSearchParams()
  if (params?.sport_key) qs.set("sport_key", params.sport_key)
  if (params?.min_profit_pct) qs.set("min_profit_pct", String(params.min_profit_pct))
  const query = qs.toString() ? `?${qs}` : ""
  return apiFetch<ArbOpportunity[]>(`/api/v1/arb/opportunities${query}`)
}

// ─── Bets ─────────────────────────────────────────────────────────────────────

export type Bet = {
  id: number
  date: string
  sport: string
  game: string
  betType: string
  odds: number
  stake: number
  result: "win" | "loss" | "pending"
  pnl: number
  closingOdds?: number
  clv?: number
}

export type BetCreate = Omit<Bet, "id" | "closingOdds" | "clv">

export async function getBets(): Promise<Bet[]> {
  return apiFetch<Bet[]>("/api/v1/bets")
}

export async function createBet(bet: BetCreate): Promise<Bet> {
  return apiFetch<Bet>("/api/v1/bets", { method: "POST", body: JSON.stringify(bet) })
}

export async function deleteBet(id: number): Promise<void> {
  await apiFetch<void>(`/api/v1/bets/${id}`, { method: "DELETE" })
}

// ─── Alerts ───────────────────────────────────────────────────────────────────

export type Alert = {
  id: number
  sport: string
  team: string
  market: string
  targetOdds: number
  direction: "above" | "below"
  active: boolean
  note: string
}

export type AlertCreate = Omit<Alert, "id" | "active">

export async function getAlerts(): Promise<Alert[]> {
  return apiFetch<Alert[]>("/api/v1/alerts")
}

export async function createAlert(alert: AlertCreate): Promise<Alert> {
  return apiFetch<Alert>("/api/v1/alerts", { method: "POST", body: JSON.stringify(alert) })
}

export async function deleteAlert(id: number): Promise<void> {
  await apiFetch<void>(`/api/v1/alerts/${id}`, { method: "DELETE" })
}

// ─── Sharp Metrics ───────────────────────────────────────────────────────────

export type LineMovementEntry = {
  game: string
  sport_key: string
  commence_time: string
  outcome: string
  betType: string
  worstOdds: number
  worstBook: string
  bestOdds: number
  bestBook: string
  disparityPct: number
  steamFlag: boolean
  bookCount: number
}

export type NoVigEntry = {
  game: string
  sport_key: string
  home_team: string
  away_team: string
  commence_time: string
  consensusFairHomeProb: number
  consensusFairAwayProb: number
  avgVigPct: number
  books: Array<{
    book: string
    homeOdds: number
    awayOdds: number
    fairHomeProb: number
    fairAwayProb: number
    vigPct: number
  }>
}

export async function getLineMovement(limit = 30): Promise<LineMovementEntry[]> {
  return apiFetch<LineMovementEntry[]>(`/api/v1/sharp/line-movement?limit=${limit}`)
}

export async function getNoVigOdds(limit = 30): Promise<NoVigEntry[]> {
  return apiFetch<NoVigEntry[]>(`/api/v1/sharp/no-vig?limit=${limit}`)
}

// ─── Admin ────────────────────────────────────────────────────────────────────

export async function triggerPoll(): Promise<{ message: string }> {
  return apiFetch<{ message: string }>("/api/v1/admin/poll", { method: "POST" })
}
