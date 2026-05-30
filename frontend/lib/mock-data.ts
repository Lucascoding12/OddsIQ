export type Game = {
  id: string
  sport: "NFL" | "NBA" | "MLB" | "NHL"
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

export const MOCK_GAMES: Game[] = [
  {
    id: "1",
    sport: "NFL",
    homeTeam: "Kansas City Chiefs",
    awayTeam: "Buffalo Bills",
    commenceTime: "2026-09-10T20:20:00Z",
    bestLine: { homeMoneyline: -150, awayMoneyline: 130, spread: -3, spreadOdds: -110, total: 47.5, overOdds: -110, underOdds: -110, book: "DraftKings" },
  },
  {
    id: "2",
    sport: "NBA",
    homeTeam: "Boston Celtics",
    awayTeam: "LA Lakers",
    commenceTime: "2026-11-01T19:00:00Z",
    bestLine: { homeMoneyline: -200, awayMoneyline: 170, spread: -5.5, spreadOdds: -108, total: 224.5, overOdds: -112, underOdds: -108, book: "FanDuel" },
  },
  {
    id: "3",
    sport: "MLB",
    homeTeam: "New York Yankees",
    awayTeam: "Boston Red Sox",
    commenceTime: "2026-07-04T19:05:00Z",
    bestLine: { homeMoneyline: -130, awayMoneyline: 110, spread: -1.5, spreadOdds: -140, total: 9, overOdds: -115, underOdds: -105, book: "BetMGM" },
  },
  {
    id: "4",
    sport: "NHL",
    homeTeam: "Toronto Maple Leafs",
    awayTeam: "Montreal Canadiens",
    commenceTime: "2026-10-15T19:30:00Z",
    bestLine: { homeMoneyline: -160, awayMoneyline: 140, spread: -1.5, spreadOdds: 120, total: 6, overOdds: -118, underOdds: -102, book: "Caesars" },
  },
]

export const MOCK_BOOK_ODDS: BookOdds[] = [
  { book: "DraftKings", homeMoneyline: -150, awayMoneyline: 130, spread: -3, spreadOdds: -110, total: 47.5, overOdds: -110, underOdds: -110 },
  { book: "FanDuel", homeMoneyline: -155, awayMoneyline: 133, spread: -3, spreadOdds: -112, total: 47.5, overOdds: -108, underOdds: -112 },
  { book: "BetMGM", homeMoneyline: -148, awayMoneyline: 128, spread: -3, spreadOdds: -110, total: 48, overOdds: -110, underOdds: -110 },
  { book: "Caesars", homeMoneyline: -152, awayMoneyline: 132, spread: -3.5, spreadOdds: -105, total: 47.5, overOdds: -112, underOdds: -108 },
  { book: "Pinnacle", homeMoneyline: -145, awayMoneyline: 138, spread: -3, spreadOdds: -107, total: 47.5, overOdds: -105, underOdds: -108 },
]

export const MOCK_ALERTS: Alert[] = [
  { id: "1", game: "Chiefs vs Bills", betType: "Away ML", targetOdds: 140, book: "any", status: "active", createdAt: "2026-05-28" },
  { id: "2", game: "Celtics vs Lakers", betType: "Home Spread -5.5", targetOdds: -108, book: "DraftKings", status: "triggered", createdAt: "2026-05-27" },
]

export const MOCK_BETS: Bet[] = [
  { id: "1", date: "2026-05-20", sport: "NFL", game: "Chiefs vs Bills", betType: "Chiefs ML", odds: -150, stake: 100, result: "win", pnl: 66.67, closingOdds: -165, clv: 15 },
  { id: "2", date: "2026-05-18", sport: "NBA", game: "Celtics vs Lakers", betType: "Celtics -5.5", odds: -108, stake: 50, result: "loss", pnl: -50, closingOdds: -112, clv: 4 },
  { id: "3", date: "2026-05-15", sport: "MLB", game: "Yankees vs Red Sox", betType: "Over 9", odds: -115, stake: 75, result: "win", pnl: 65.22, closingOdds: -118, clv: 3 },
  { id: "4", date: "2026-05-29", sport: "NHL", game: "Leafs vs Habs", betType: "Leafs ML", odds: -160, stake: 100, result: "pending", pnl: 0, closingOdds: -160, clv: 0 },
]
