export type Game = {
  id: string
  sport: string
  sportKey: string
  category: string
  homeTeam: string
  awayTeam: string
  commenceTime: string
  bestLine: {
    homeMoneyline: number
    awayMoneyline: number
    spread: number
    spreadOdds: number
    total: number
    overOdds: number
    underOdds: number
    book: string
  }
}

export type BookOdds = {
  book: string
  homeMoneyline: number
  awayMoneyline: number
  spread: number
  spreadOdds: number
  total: number
  overOdds: number
  underOdds: number
}

export type Alert = {
  id: string
  game: string
  betType: string
  targetOdds: number
  book: string | "any"
  status: "active" | "triggered"
  createdAt: string
}

export type Bet = {
  id: string
  date: string
  sport: string
  game: string
  betType: string
  odds: number
  stake: number
  result: "win" | "loss" | "pending"
  pnl: number
  closingOdds: number
  clv: number
}

