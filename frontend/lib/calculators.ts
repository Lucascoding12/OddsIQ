// All odds math — pure functions, no side effects

// ── Core conversions ─────────────────────────────────────────────────────────

export function impliedProbability(americanOdds: number): number {
  if (americanOdds > 0) return 100 / (americanOdds + 100)
  return Math.abs(americanOdds) / (Math.abs(americanOdds) + 100)
}

export function toDecimal(americanOdds: number): number {
  if (americanOdds > 0) return americanOdds / 100 + 1
  return 100 / Math.abs(americanOdds) + 1
}

export function decimalToAmerican(decimal: number): number {
  if (decimal >= 2) return (decimal - 1) * 100
  return -100 / (decimal - 1)
}

export function impliedProbFromDecimal(decimal: number): number {
  return 1 / decimal
}

export function formatOdds(odds: number): string {
  if (!isFinite(odds)) return "N/A"
  return odds >= 0 ? `+${Math.round(odds)}` : `${Math.round(odds)}`
}

// ── No-Vig ───────────────────────────────────────────────────────────────────

export function removeVig(probabilities: number[]): number[] {
  const total = probabilities.reduce((a, b) => a + b, 0)
  return probabilities.map((p) => p / total)
}

export function fairOdds(p: number): number {
  if (p >= 1) return -Infinity
  if (p <= 0) return Infinity
  if (p < 0.5) return (1 / p - 1) * 100
  return -(100 * p) / (1 - p)
}

// ── Hold / Vig ───────────────────────────────────────────────────────────────

export function holdPct(decimalOddsArr: number[]): number {
  const total = decimalOddsArr.reduce((sum, d) => sum + 1 / d, 0)
  return (total - 1) * 100
}

// ── EV ───────────────────────────────────────────────────────────────────────

export function expectedValue(stake: number, americanOdds: number, trueProbability: number): {
  ev: number
  roi: number
  profit: number
} {
  const decimal = toDecimal(americanOdds)
  const profit = stake * (decimal - 1)
  const ev = trueProbability * profit - (1 - trueProbability) * stake
  return { ev, roi: ev / stake, profit }
}

// ── Kelly ────────────────────────────────────────────────────────────────────

export function kelly(americanOdds: number, trueProbability: number): {
  full: number
  half: number
  quarter: number
} {
  const b = toDecimal(americanOdds) - 1
  const p = trueProbability
  const q = 1 - p
  const full = Math.max(0, (b * p - q) / b)
  return { full, half: full * 0.5, quarter: full * 0.25 }
}

// ── Arbitrage ────────────────────────────────────────────────────────────────

export function arbProfit(americanOddsArr: number[]): {
  exists: boolean
  totalProb: number
  profitPct: number
} {
  const totalProb = americanOddsArr.reduce((sum, o) => sum + impliedProbability(o), 0)
  return { exists: totalProb < 1, totalProb, profitPct: (1 - totalProb) * 100 }
}

export function arbStakes(americanOddsArr: number[], bankroll: number): number[] {
  const decimals = americanOddsArr.map(toDecimal)
  const invOdds = decimals.map((d) => 1 / d)
  const sumInv = invOdds.reduce((a, b) => a + b, 0)
  return invOdds.map((inv) => (inv / sumInv) * bankroll)
}

// ── CLV ──────────────────────────────────────────────────────────────────────

export function clv(betOdds: number, closingOdds: number): {
  clvOdds: number
  clvPct: number
} {
  const betProb = impliedProbability(betOdds)
  const closeProb = impliedProbability(closingOdds)
  return { clvOdds: closingOdds - betOdds, clvPct: (closeProb - betProb) * 100 }
}

// ── Bonus Bet Conversion ─────────────────────────────────────────────────────

export function bonusBetConversion(bonusAmount: number, cashout: number): {
  conversionPct: number
  profit: number
} {
  return {
    conversionPct: bonusAmount > 0 ? (cashout / bonusAmount) * 100 : 0,
    profit: cashout,
  }
}

// Best odds to convert a bonus bet to cash (lay at given odds)
export function bonusBetOptimalCashout(bonusAmount: number, americanOdds: number): number {
  const decimal = toDecimal(americanOdds)
  // free bet SNR: profit only if win, so cashout = bonus * (decimal-1) * layFactor
  // simplified: guaranteed cash = bonus * (decimal-1) / decimal
  return bonusAmount * (decimal - 1) / decimal
}

// ── Parlay ───────────────────────────────────────────────────────────────────

export function parlayDecimalOdds(decimalLegs: number[]): number {
  return decimalLegs.reduce((acc, d) => acc * d, 1)
}

export function parlayPayout(stake: number, decimalLegs: number[]): number {
  return stake * parlayDecimalOdds(decimalLegs)
}

// ── Prediction Market ────────────────────────────────────────────────────────

export function predictionMarketConvert(price: number): {
  probability: number
  decimalOdds: number
  americanOdds: number
} {
  const p = price / 100
  const decimal = 1 / p
  return { probability: p, decimalOdds: decimal, americanOdds: decimalToAmerican(decimal) }
}

// ── Point Spread ─────────────────────────────────────────────────────────────

// Standard normal CDF approximation (Abramowitz & Stegun)
function normalCDF(x: number): number {
  const t = 1 / (1 + 0.2316419 * Math.abs(x))
  const d = 0.3989423 * Math.exp(-x * x / 2)
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.7814779 + t * (-1.8212560 + t * 1.3302744))))
  return x > 0 ? 1 - p : p
}

// sigma: NFL ≈ 13.45, NBA ≈ 11, MLB ≈ 1.5, NHL ≈ 1.2
export function spreadWinProbability(spread: number, sigma: number): number {
  return normalCDF(spread / sigma)
}

export function spreadToMoneyline(spread: number, sigma: number): number {
  const p = spreadWinProbability(spread, sigma)
  return decimalToAmerican(1 / p)
}

// ── Poisson ──────────────────────────────────────────────────────────────────

export function poissonProbability(lambda: number, k: number): number {
  if (lambda <= 0 || k < 0) return 0
  let logP = -lambda + k * Math.log(lambda)
  for (let i = 1; i <= k; i++) logP -= Math.log(i)
  return Math.exp(logP)
}

export function poissonDistribution(lambda: number, maxK = 10): Array<{ k: number; prob: number }> {
  return Array.from({ length: maxK + 1 }, (_, k) => ({
    k,
    prob: poissonProbability(lambda, k),
  }))
}

// ── Round Robin ──────────────────────────────────────────────────────────────

export function combinations(n: number, r: number): number {
  if (r > n || r < 0) return 0
  if (r === 0 || r === n) return 1
  let result = 1
  for (let i = 0; i < Math.min(r, n - r); i++) {
    result = (result * (n - i)) / (i + 1)
  }
  return Math.round(result)
}

export function roundRobinParlays(
  decimalLegs: number[],
  size: number,
  stake: number
): {
  numParlays: number
  totalStake: number
  maxPayout: number
  avgPayout: number
} {
  const n = decimalLegs.length
  const numParlays = combinations(n, size)
  // generate all combos and compute avg payout
  const combos: number[][] = []
  function combine(start: number, current: number[]) {
    if (current.length === size) { combos.push([...current]); return }
    for (let i = start; i < n; i++) combine(i + 1, [...current, decimalLegs[i]])
  }
  combine(0, [])
  const payouts = combos.map((c) => stake * c.reduce((a, b) => a * b, 1))
  const maxPayout = Math.max(...payouts)
  const avgPayout = payouts.reduce((a, b) => a + b, 0) / payouts.length
  return { numParlays, totalStake: numParlays * stake, maxPayout, avgPayout }
}
