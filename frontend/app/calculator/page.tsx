"use client"

import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useState } from "react"
import {
  impliedProbability, removeVig, fairOdds, formatOdds,
  toDecimal, decimalToAmerican, holdPct,
  expectedValue, kelly, arbProfit, arbStakes, clv,
  bonusBetConversion, bonusBetOptimalCashout,
  parlayDecimalOdds, parlayPayout,
  predictionMarketConvert,
  spreadWinProbability, spreadToMoneyline,
  poissonDistribution,
  combinations, roundRobinParlays,
} from "@/lib/calculators"

const CALCS = [
  "Implied Probability",
  "No-Vig Fair Odds",
  "Expected Value",
  "Kelly Criterion",
  "Arbitrage",
  "CLV",
  "Hold",
  "Vig",
  "Bonus Bet",
  "Odds Converter",
  "Parlay",
  "Prediction Market",
  "Point Spread",
  "Poisson",
  "Round Robin",
] as const
type Calc = (typeof CALCS)[number]

// ── Shared primitives ────────────────────────────────────────────────────────
function FormRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b last:border-0">
      <span className="text-sm text-muted-foreground shrink-0 w-44">{label}</span>
      {children}
    </div>
  )
}

function NumInput(props: React.InputHTMLAttributes<HTMLInputElement> & { prefix?: string; suffix?: string }) {
  const { prefix, suffix, className, ...rest } = props
  return (
    <div className="flex items-center gap-1 justify-end">
      {prefix && <span className="text-sm text-muted-foreground">{prefix}</span>}
      <input
        {...rest}
        className={`w-32 border rounded px-2 py-1.5 text-sm font-mono text-right bg-background focus:outline-none focus:ring-1 focus:ring-ring ${className ?? ""}`}
      />
      {suffix && <span className="text-sm text-muted-foreground">{suffix}</span>}
    </div>
  )
}

function Metric({ label, value, positive }: { label: string; value: string; positive?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5 min-w-0">
      <span className="text-xs text-muted-foreground truncate">{label}</span>
      <span className={`text-base font-semibold font-mono ${positive === true ? "text-blue-300" : positive === false ? "text-red-500" : ""}`}>
        {value}
      </span>
    </div>
  )
}

function MetricsRow({ children }: { children: React.ReactNode }) {
  return <div className="pt-3 flex flex-wrap gap-6 border-t mt-1">{children}</div>
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border bg-card p-5 max-w-lg space-y-0.5">{children}</div>
}

function InlineTable({ headers, children, footer }: {
  headers: string[]
  children: React.ReactNode
  footer?: React.ReactNode
}) {
  return (
    <div className="rounded-lg border bg-card overflow-hidden max-w-lg">
      <div className={`grid bg-muted/50 border-b px-4 py-2 text-xs font-medium text-muted-foreground`}
        style={{ gridTemplateColumns: `repeat(${headers.length}, 1fr)` }}>
        {headers.map((h, i) => (
          <span key={h} className={i === 0 ? "" : i === headers.length - 1 ? "text-right" : "text-center"}>{h}</span>
        ))}
      </div>
      {children}
      {footer && <div className="px-4 py-2 bg-muted/30 border-t text-xs text-muted-foreground flex justify-between">{footer}</div>}
    </div>
  )
}

// ── 1. Implied Probability ───────────────────────────────────────────────────
function ImpliedProbCalc() {
  const [odds, setOdds] = useState("150")
  const o = Number(odds)
  const valid = odds !== "" && !isNaN(o) && o !== 0
  const prob = valid ? impliedProbability(o) : null
  const dec = valid ? toDecimal(o) : null

  return (
    <Card>
      <FormRow label="American Odds"><NumInput value={odds} onChange={(e) => setOdds(e.target.value)} placeholder="+150" /></FormRow>
      <MetricsRow>
        <Metric label="Implied Probability" value={prob != null ? `${(prob * 100).toFixed(2)}%` : "—"} positive={prob != null} />
        <Metric label="Decimal Odds" value={dec != null ? dec.toFixed(3) : "—"} />
        <Metric label="Break-even %" value={prob != null ? `${(prob * 100).toFixed(2)}%` : "—"} />
      </MetricsRow>
    </Card>
  )
}

// ── 2. No-Vig ────────────────────────────────────────────────────────────────
function NoVigCalc() {
  const [sides, setSides] = useState([{ odds: "110" }, { odds: "110" }])
  const parsed = sides.map((s) => Number(s.odds || "0"))
  const valid = parsed.every((o) => !isNaN(o) && o !== 0)
  const probs = valid ? parsed.map(impliedProbability) : []
  const totalProb = probs.reduce((a, b) => a + b, 0)
  const fairProbs = valid ? removeVig(probs) : []

  return (
    <InlineTable
      headers={["Odds", "No-Vig %", "No-Vig Odds"]}
      footer={<>
        <div className="flex gap-3">
          {sides.length < 4 && <button onClick={() => setSides((p) => [...p, { odds: "" }])} className="hover:text-foreground">+ Add side</button>}
          {sides.length > 2 && <button onClick={() => setSides((p) => p.slice(0, -1))} className="hover:text-foreground">− Remove</button>}
        </div>
        {valid && <span>Hold: <span className="font-mono font-medium">{((totalProb - 1) * 100).toFixed(2)}%</span></span>}
      </>}
    >
      {sides.map((s, i) => (
        <div key={i} className="grid grid-cols-3 items-center px-4 py-3 border-b last:border-0">
          <input className="w-24 border rounded px-2 py-1.5 text-sm font-mono bg-background focus:outline-none focus:ring-1 focus:ring-ring"
            placeholder="+110" value={s.odds}
            onChange={(e) => setSides((prev) => prev.map((x, idx) => idx === i ? { odds: e.target.value } : x))} />
          <div className="text-center font-mono text-sm">{fairProbs[i] != null ? `${(fairProbs[i] * 100).toFixed(2)}%` : "—"}</div>
          <div className="text-right font-mono text-sm font-medium text-blue-300">{fairProbs[i] != null ? formatOdds(fairOdds(fairProbs[i])) : "—"}</div>
        </div>
      ))}
    </InlineTable>
  )
}

// ── 3. EV ────────────────────────────────────────────────────────────────────
function EVCalc() {
  const [wager, setWager] = useState("100")
  const [odds, setOdds] = useState("110")
  const [winPct, setWinPct] = useState("60")
  const w = Number(wager), o = Number(odds), p = Number(winPct) / 100
  const valid = w > 0 && o !== 0 && !isNaN(o) && p > 0 && p < 1
  const result = valid ? expectedValue(w, o, p) : null

  return (
    <Card>
      <FormRow label="Wager"><NumInput prefix="$" value={wager} onChange={(e) => setWager(e.target.value)} placeholder="100" /></FormRow>
      <FormRow label="Odds"><NumInput value={odds} onChange={(e) => setOdds(e.target.value)} placeholder="+110" /></FormRow>
      <FormRow label="Win Probability"><NumInput value={winPct} onChange={(e) => setWinPct(e.target.value)} placeholder="60" suffix="%" /></FormRow>
      <MetricsRow>
        <Metric label="Expected Value" value={result ? `${result.ev >= 0 ? "+" : ""}$${result.ev.toFixed(2)}` : "$0.00"} positive={result ? result.ev > 0 : undefined} />
        <Metric label="ROI" value={result ? `${(result.roi * 100).toFixed(2)}%` : "0.00%"} positive={result ? result.roi > 0 : undefined} />
        <Metric label="Profit if Win" value={result ? `$${result.profit.toFixed(2)}` : "$0.00"} />
      </MetricsRow>
    </Card>
  )
}

// ── 4. Kelly ─────────────────────────────────────────────────────────────────
function KellyCalc() {
  const [multiplier, setMultiplier] = useState("0.25")
  const [odds, setOdds] = useState("110")
  const [winPct, setWinPct] = useState("60")
  const [bankroll, setBankroll] = useState("5000")
  const mult = Number(multiplier), o = Number(odds), p = Number(winPct) / 100, b = Number(bankroll)
  const valid = o !== 0 && !isNaN(o) && p > 0 && p < 1 && mult > 0
  const k = valid ? kelly(o, p) : null
  const adjusted = k ? k.full * mult : 0
  const evResult = valid ? expectedValue(100, o, p) : null

  return (
    <Card>
      <FormRow label="Kelly Multiplier"><NumInput value={multiplier} onChange={(e) => setMultiplier(e.target.value)} placeholder="0.25" /></FormRow>
      <FormRow label="Odds"><NumInput value={odds} onChange={(e) => setOdds(e.target.value)} placeholder="+110" /></FormRow>
      <FormRow label="Win %"><NumInput value={winPct} onChange={(e) => setWinPct(e.target.value)} placeholder="60" suffix="%" /></FormRow>
      <FormRow label="Bankroll"><NumInput prefix="$" value={bankroll} onChange={(e) => setBankroll(e.target.value)} placeholder="5000" /></FormRow>
      <MetricsRow>
        <Metric label="Expected Value" value={evResult ? `${(evResult.roi * 100).toFixed(2)}%` : "0.00%"} positive={evResult ? evResult.ev > 0 : undefined} />
        <Metric label="Fraction of Bankroll" value={k ? `${(adjusted * 100).toFixed(2)}%` : "0.00%"} positive={k ? k.full > 0 : undefined} />
        <Metric label="Amount to Wager" value={k && b > 0 ? `$${(adjusted * b).toFixed(2)}` : "$0.00"} positive={k ? k.full > 0 : undefined} />
      </MetricsRow>
    </Card>
  )
}

// ── 5. Arbitrage ─────────────────────────────────────────────────────────────
function ArbCalc() {
  const [legs, setLegs] = useState([{ odds: "110", book: "" }, { odds: "110", book: "" }])
  const [bankroll, setBankroll] = useState("1000")
  const parsedOdds = legs.map((l) => Number(l.odds || "0"))
  const valid = parsedOdds.every((o) => !isNaN(o) && o !== 0)
  const arb = valid ? arbProfit(parsedOdds) : null
  const b = Number(bankroll)
  const stakes = valid && b > 0 ? arbStakes(parsedOdds, b) : []

  return (
    <InlineTable
      headers={["Odds", "Book", "Stake"]}
      footer={<>
        <div className="flex gap-3 items-center">
          {legs.length < 6 && <button onClick={() => setLegs((p) => [...p, { odds: "", book: "" }])} className="hover:text-foreground">+ Leg</button>}
          {legs.length > 2 && <button onClick={() => setLegs((p) => p.slice(0, -1))} className="hover:text-foreground">− Leg</button>}
          <span>Bankroll: <input className="w-20 border rounded px-2 py-0.5 font-mono bg-background focus:outline-none focus:ring-1 focus:ring-ring ml-1"
            value={bankroll} onChange={(e) => setBankroll(e.target.value)} placeholder="1000" /></span>
        </div>
        {arb && <span className={arb.exists ? "text-blue-300 font-medium" : ""}>
          {arb.exists ? `+${arb.profitPct.toFixed(2)}% arb profit` : `${(arb.totalProb * 100).toFixed(2)}% total prob`}
        </span>}
      </>}
    >
      {legs.map((l, i) => (
        <div key={i} className="grid grid-cols-3 items-center gap-2 px-4 py-3 border-b last:border-0">
          <input className="w-24 border rounded px-2 py-1.5 text-sm font-mono bg-background focus:outline-none focus:ring-1 focus:ring-ring"
            placeholder="+110" value={l.odds}
            onChange={(e) => setLegs((p) => p.map((x, idx) => idx === i ? { ...x, odds: e.target.value } : x))} />
          <input className="w-full border rounded px-2 py-1.5 text-sm bg-background focus:outline-none focus:ring-1 focus:ring-ring"
            placeholder="DraftKings" value={l.book}
            onChange={(e) => setLegs((p) => p.map((x, idx) => idx === i ? { ...x, book: e.target.value } : x))} />
          <div className="text-right font-mono text-sm font-medium">{stakes[i] != null ? `$${stakes[i].toFixed(2)}` : "—"}</div>
        </div>
      ))}
    </InlineTable>
  )
}

// ── 6. CLV ───────────────────────────────────────────────────────────────────
function CLVCalc() {
  const [betOdds, setBetOdds] = useState("120")
  const [closingOdds, setClosingOdds] = useState("100")
  const b = Number(betOdds), c = Number(closingOdds)
  const valid = b !== 0 && c !== 0 && !isNaN(b) && !isNaN(c)
  const result = valid ? clv(b, c) : null

  return (
    <Card>
      <FormRow label="Odds You Bet"><NumInput value={betOdds} onChange={(e) => setBetOdds(e.target.value)} placeholder="+120" /></FormRow>
      <FormRow label="Closing Odds"><NumInput value={closingOdds} onChange={(e) => setClosingOdds(e.target.value)} placeholder="+100" /></FormRow>
      <MetricsRow>
        <Metric label="CLV (odds)" value={result ? `${result.clvOdds >= 0 ? "+" : ""}${result.clvOdds.toFixed(0)}` : "—"} positive={result ? result.clvOdds > 0 : undefined} />
        <Metric label="CLV (probability)" value={result ? `${result.clvPct >= 0 ? "+" : ""}${result.clvPct.toFixed(2)}%` : "—"} positive={result ? result.clvPct > 0 : undefined} />
        <Metric label="Assessment" value={result ? (result.clvPct > 0 ? "Beat market" : result.clvPct < 0 ? "Behind market" : "At market") : "—"} positive={result ? result.clvPct > 0 : result ? false : undefined} />
      </MetricsRow>
    </Card>
  )
}

// ── 7. Hold / 8. Vig (same formula, different framing) ──────────────────────
function HoldVigCalc({ mode }: { mode: "hold" | "vig" }) {
  const [sides, setSides] = useState([{ odds: "-110" }, { odds: "-110" }])
  const parsed = sides.map((s) => {
    const n = Number(s.odds || "0")
    return !isNaN(n) && n !== 0 ? toDecimal(n) : null
  })
  const valid = parsed.every((d) => d !== null)
  const hold = valid ? holdPct(parsed as number[]) : null

  return (
    <InlineTable
      headers={["American Odds", "Decimal", "Implied Prob"]}
      footer={<>
        <div className="flex gap-3">
          {sides.length < 4 && <button onClick={() => setSides((p) => [...p, { odds: "" }])} className="hover:text-foreground">+ Side</button>}
          {sides.length > 2 && <button onClick={() => setSides((p) => p.slice(0, -1))} className="hover:text-foreground">− Side</button>}
        </div>
        {hold !== null && (
          <span>{mode === "hold" ? "Sportsbook Hold" : "Vig"}: <span className="font-mono font-medium">{hold.toFixed(2)}%</span></span>
        )}
      </>}
    >
      {sides.map((s, i) => {
        const n = Number(s.odds || "0")
        const dec = !isNaN(n) && n !== 0 ? toDecimal(n) : null
        const prob = dec ? 1 / dec : null
        return (
          <div key={i} className="grid grid-cols-3 items-center px-4 py-3 border-b last:border-0">
            <input className="w-28 border rounded px-2 py-1.5 text-sm font-mono bg-background focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="-110" value={s.odds}
              onChange={(e) => setSides((prev) => prev.map((x, idx) => idx === i ? { odds: e.target.value } : x))} />
            <div className="text-center font-mono text-sm">{dec ? dec.toFixed(3) : "—"}</div>
            <div className="text-right font-mono text-sm">{prob ? `${(prob * 100).toFixed(2)}%` : "—"}</div>
          </div>
        )
      })}
    </InlineTable>
  )
}

// ── 9. Bonus Bet Conversion ──────────────────────────────────────────────────
function BonusBetCalc() {
  const [bonus, setBonus] = useState("100")
  const [odds, setOdds] = useState("200")
  const b = Number(bonus), o = Number(odds)
  const valid = b > 0 && o !== 0 && !isNaN(o)
  const optimal = valid ? bonusBetOptimalCashout(b, o) : null
  const pct = optimal != null ? bonusBetConversion(b, optimal) : null

  return (
    <Card>
      <FormRow label="Bonus Bet Amount"><NumInput prefix="$" value={bonus} onChange={(e) => setBonus(e.target.value)} placeholder="100" /></FormRow>
      <FormRow label="Odds to Convert At">
        <NumInput value={odds} onChange={(e) => setOdds(e.target.value)} placeholder="+200" />
      </FormRow>
      <p className="text-xs text-muted-foreground pt-1">Place bonus bet at these odds, lay the other side for guaranteed cash.</p>
      <MetricsRow>
        <Metric label="Guaranteed Cashout" value={optimal != null ? `$${optimal.toFixed(2)}` : "—"} positive={optimal != null} />
        <Metric label="Conversion %" value={pct ? `${pct.conversionPct.toFixed(1)}%` : "—"} positive={pct ? pct.conversionPct > 60 : undefined} />
        <Metric label="Profit vs 0" value={optimal != null ? `$${optimal.toFixed(2)}` : "—"} positive={optimal != null} />
      </MetricsRow>
    </Card>
  )
}

// ── 10. Odds Converter ────────────────────────────────────────────────────────
function OddsConverterCalc() {
  const [american, setAmerican] = useState("150")
  const o = Number(american)
  const valid = american !== "" && !isNaN(o) && o !== 0
  const dec = valid ? toDecimal(o) : null
  const prob = valid ? impliedProbability(o) : null

  return (
    <Card>
      <FormRow label="American Odds"><NumInput value={american} onChange={(e) => setAmerican(e.target.value)} placeholder="+150" /></FormRow>
      <MetricsRow>
        <Metric label="Decimal" value={dec ? dec.toFixed(4) : "—"} />
        <Metric label="Implied Prob" value={prob ? `${(prob * 100).toFixed(2)}%` : "—"} />
        <Metric label="Fractional" value={dec ? (() => {
          const n = dec - 1
          const gcd = (a: number, b: number): number => b < 0.001 ? a : gcd(b, a % b)
          const d = 100, num = Math.round(n * d)
          const g = gcd(num, d)
          return `${num / g}/${d / g}`
        })() : "—"} />
      </MetricsRow>
      {dec && (
        <div className="pt-3 border-t mt-2 space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Decimal → American</span>
            <span className="font-mono">{formatOdds(decimalToAmerican(dec))}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Fair odds (no-vig 2-way)</span>
            <span className="font-mono">{prob ? formatOdds(fairOdds(prob / (2 * prob))) : "—"}</span>
          </div>
        </div>
      )}
    </Card>
  )
}

// ── 11. Parlay ────────────────────────────────────────────────────────────────
function ParlayCalc() {
  const [legs, setLegs] = useState([{ odds: "-110" }, { odds: "-110" }, { odds: "-110" }])
  const [stake, setStake] = useState("100")
  const parsed = legs.map((l) => {
    const n = Number(l.odds || "0")
    return !isNaN(n) && n !== 0 ? toDecimal(n) : null
  })
  const valid = parsed.every((d) => d !== null)
  const totalDec = valid ? parlayDecimalOdds(parsed as number[]) : null
  const payout = valid ? parlayPayout(Number(stake), parsed as number[]) : null
  const impliedProb = totalDec ? 1 / totalDec : null
  const americanOdds = totalDec ? decimalToAmerican(totalDec) : null

  return (
    <InlineTable
      headers={["Leg Odds", "Decimal", ""]}
      footer={<>
        <div className="flex gap-3 items-center">
          {legs.length < 12 && <button onClick={() => setLegs((p) => [...p, { odds: "" }])} className="hover:text-foreground">+ Leg</button>}
          {legs.length > 2 && <button onClick={() => setLegs((p) => p.slice(0, -1))} className="hover:text-foreground">− Leg</button>}
          <span>Stake: <input className="w-20 border rounded px-2 py-0.5 font-mono bg-background focus:outline-none focus:ring-1 focus:ring-ring ml-1"
            value={stake} onChange={(e) => setStake(e.target.value)} placeholder="100" /></span>
        </div>
        <div className="text-right space-y-0.5">
          {totalDec && <div>Parlay odds: <span className="font-mono font-medium">{formatOdds(americanOdds!)}</span></div>}
          {payout && <div>Payout: <span className="font-mono font-medium text-blue-300">${payout.toFixed(2)}</span></div>}
        </div>
      </>}
    >
      {legs.map((l, i) => {
        const n = Number(l.odds || "0")
        const dec = !isNaN(n) && n !== 0 ? toDecimal(n) : null
        return (
          <div key={i} className="grid grid-cols-3 items-center px-4 py-3 border-b last:border-0">
            <input className="w-24 border rounded px-2 py-1.5 text-sm font-mono bg-background focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="-110" value={l.odds}
              onChange={(e) => setLegs((p) => p.map((x, idx) => idx === i ? { odds: e.target.value } : x))} />
            <div className="text-center font-mono text-sm">{dec ? dec.toFixed(3) : "—"}</div>
            <div className="text-right text-xs text-muted-foreground">{dec ? `${(100 / dec).toFixed(1)}%` : ""}</div>
          </div>
        )
      })}
    </InlineTable>
  )
}

// ── 12. Prediction Market Converter ──────────────────────────────────────────
function PredictionMarketCalc() {
  const [price, setPrice] = useState("65")
  const p = Number(price)
  const valid = p > 0 && p < 100
  const result = valid ? predictionMarketConvert(p) : null

  return (
    <Card>
      <FormRow label="Market Price (¢)">
        <NumInput value={price} onChange={(e) => setPrice(e.target.value)} placeholder="65" suffix="¢" />
      </FormRow>
      <p className="text-xs text-muted-foreground">Kalshi / Polymarket price in cents (1–99)</p>
      <MetricsRow>
        <Metric label="Probability" value={result ? `${(result.probability * 100).toFixed(1)}%` : "—"} />
        <Metric label="Decimal Odds" value={result ? result.decimalOdds.toFixed(3) : "—"} />
        <Metric label="American Odds" value={result ? formatOdds(result.americanOdds) : "—"} />
      </MetricsRow>
      {result && (
        <div className="pt-2 border-t mt-2 text-sm flex justify-between">
          <span className="text-muted-foreground">NO side implied</span>
          <span className="font-mono">{`${(100 - p).toFixed(1)}%`} / {formatOdds(decimalToAmerican(1 / (1 - result.probability)))}</span>
        </div>
      )}
    </Card>
  )
}

// ── 13. Point Spread ──────────────────────────────────────────────────────────
const SPORT_SIGMAS: Record<string, number> = { NFL: 13.45, NBA: 11.0, MLB: 1.5, NHL: 1.2, NCAA: 16.0 }

function PointSpreadCalc() {
  const [spread, setSpread] = useState("3")
  const [sport, setSport] = useState("NFL")
  const s = Number(spread)
  const sigma = SPORT_SIGMAS[sport]
  const valid = !isNaN(s) && spread !== ""
  const prob = valid ? spreadWinProbability(s, sigma) : null
  const ml = valid ? spreadToMoneyline(s, sigma) : null

  return (
    <Card>
      <FormRow label="Point Spread">
        <NumInput value={spread} onChange={(e) => setSpread(e.target.value)} placeholder="3" />
      </FormRow>
      <FormRow label="Sport">
        <select className="border rounded px-2 py-1.5 text-sm bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          value={sport} onChange={(e) => setSport(e.target.value)}>
          {Object.keys(SPORT_SIGMAS).map((s) => <option key={s}>{s}</option>)}
        </select>
      </FormRow>
      <p className="text-xs text-muted-foreground">σ = {sigma} (standard deviation for {sport})</p>
      <MetricsRow>
        <Metric label="Favorite Cover %" value={prob ? `${(prob * 100).toFixed(2)}%` : "—"} />
        <Metric label="Implied Moneyline" value={ml ? formatOdds(ml) : "—"} />
        <Metric label="Dog Win %" value={prob ? `${((1 - prob) * 100).toFixed(2)}%` : "—"} />
      </MetricsRow>
    </Card>
  )
}

// ── 14. Poisson ───────────────────────────────────────────────────────────────
function PoissonCalc() {
  const [lambda, setLambda] = useState("1.8")
  const [target, setTarget] = useState("2")
  const l = Number(lambda), k = Number(target)
  const valid = l > 0 && !isNaN(l) && k >= 0 && !isNaN(k) && Number.isInteger(k)
  const dist = valid ? poissonDistribution(l, Math.min(10, Math.max(k + 3, 7))) : []
  const targetRow = dist.find((d) => d.k === k)
  const cumUnder = dist.filter((d) => d.k < k).reduce((s, d) => s + d.prob, 0)
  const cumOver = dist.filter((d) => d.k > k).reduce((s, d) => s + d.prob, 0)

  return (
    <Card>
      <FormRow label="Expected Goals (λ)"><NumInput value={lambda} onChange={(e) => setLambda(e.target.value)} placeholder="1.8" /></FormRow>
      <FormRow label="Exact Goals (k)"><NumInput value={target} onChange={(e) => setTarget(e.target.value)} placeholder="2" /></FormRow>
      <MetricsRow>
        <Metric label={`P(exactly ${k})`} value={targetRow ? `${(targetRow.prob * 100).toFixed(3)}%` : "—"} positive={targetRow != null} />
        <Metric label={`P(under ${k})`} value={valid ? `${(cumUnder * 100).toFixed(2)}%` : "—"} />
        <Metric label={`P(over ${k})`} value={valid ? `${(cumOver * 100).toFixed(2)}%` : "—"} />
      </MetricsRow>
      {dist.length > 0 && (
        <div className="pt-3 border-t mt-2 space-y-1">
          {dist.slice(0, 8).map((d) => (
            <div key={d.k} className="flex justify-between text-xs">
              <span className="text-muted-foreground">P(k={d.k})</span>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-muted rounded-full h-1.5">
                  <div className="bg-green-600 h-1.5 rounded-full" style={{ width: `${Math.min(100, d.prob * 300)}%` }} />
                </div>
                <span className={`font-mono w-14 text-right ${d.k === k ? "font-semibold text-blue-300" : ""}`}>{(d.prob * 100).toFixed(3)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

// ── 15. Round Robin ───────────────────────────────────────────────────────────
function RoundRobinCalc() {
  const [legs, setLegs] = useState([{ odds: "-110" }, { odds: "-110" }, { odds: "-110" }, { odds: "-110" }, { odds: "-110" }])
  const [size, setSize] = useState("3")
  const [stake, setStake] = useState("10")
  const r = Number(size), s = Number(stake)
  const parsed = legs.map((l) => {
    const n = Number(l.odds || "0")
    return !isNaN(n) && n !== 0 ? toDecimal(n) : null
  })
  const valid = parsed.every((d) => d !== null) && r >= 2 && r <= legs.length && s > 0
  const result = valid ? roundRobinParlays(parsed as number[], r, s) : null
  const numCombos = combinations(legs.length, r)

  return (
    <div className="max-w-lg space-y-4">
      <InlineTable headers={["Leg Odds", "Decimal", ""]}>
        {legs.map((l, i) => {
          const n = Number(l.odds || "0")
          const dec = !isNaN(n) && n !== 0 ? toDecimal(n) : null
          return (
            <div key={i} className="grid grid-cols-3 items-center px-4 py-3 border-b last:border-0">
              <input className="w-24 border rounded px-2 py-1.5 text-sm font-mono bg-background focus:outline-none focus:ring-1 focus:ring-ring"
                placeholder="-110" value={l.odds}
                onChange={(e) => setLegs((p) => p.map((x, idx) => idx === i ? { odds: e.target.value } : x))} />
              <div className="text-center font-mono text-sm">{dec ? dec.toFixed(3) : "—"}</div>
              <div className="text-right">
                {legs.length > 3 && (
                  <button onClick={() => setLegs((p) => p.filter((_, idx) => idx !== i))} className="text-xs text-muted-foreground hover:text-foreground">✕</button>
                )}
              </div>
            </div>
          )
        })}
      </InlineTable>
      <div className="flex flex-wrap gap-3 items-center text-sm">
        {legs.length < 10 && (
          <button onClick={() => setLegs((p) => [...p, { odds: "-110" }])} className="border rounded px-2 py-1 text-xs text-muted-foreground hover:text-foreground">+ Leg</button>
        )}
        <span className="text-muted-foreground">Parlay size:</span>
        <select className="border rounded px-2 py-1 text-sm bg-background focus:outline-none"
          value={size} onChange={(e) => setSize(e.target.value)}>
          {Array.from({ length: Math.max(0, legs.length - 1) }, (_, i) => i + 2).map((n) => (
            <option key={n}>{n}</option>
          ))}
        </select>
        <span className="text-muted-foreground">Stake per parlay: $</span>
        <input className="w-16 border rounded px-2 py-1 text-sm font-mono bg-background focus:outline-none"
          value={stake} onChange={(e) => setStake(e.target.value)} />
      </div>
      <div className="rounded-lg border bg-card p-4">
        <MetricsRow>
          <Metric label="Parlays Generated" value={`${numCombos}`} />
          <Metric label="Total Stake" value={result ? `$${result.totalStake.toFixed(2)}` : "—"} />
          <Metric label="Max Payout" value={result ? `$${result.maxPayout.toFixed(2)}` : "—"} positive={result != null} />
          <Metric label="Avg Payout" value={result ? `$${result.avgPayout.toFixed(2)}` : "—"} />
        </MetricsRow>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
const TITLES: Record<Calc, string> = {
  "Implied Probability": "Implied Probability Calculator",
  "No-Vig Fair Odds": "No-Vig Fair Odds Calculator",
  "Expected Value": "Expected Value (EV) Calculator",
  "Kelly Criterion": "Kelly Criterion Calculator",
  "Arbitrage": "Arbitrage Calculator",
  "CLV": "Closing Line Value Calculator",
  "Hold": "Hold Calculator",
  "Vig": "Vig Calculator",
  "Bonus Bet": "Bonus Bet Conversion Calculator",
  "Odds Converter": "Odds Converter Calculator",
  "Parlay": "Parlay Calculator",
  "Prediction Market": "Prediction Market Converter",
  "Point Spread": "Point Spread Calculator",
  "Poisson": "Poisson Calculator",
  "Round Robin": "Round Robin Calculator",
}

const DESCRIPTIONS: Record<Calc, string> = {
  "Implied Probability": "Convert American odds to the sportsbook's implied win probability.",
  "No-Vig Fair Odds": "Strip the sportsbook margin to find the true fair odds for each side.",
  "Expected Value": "Calculate the expected profit of a bet given your true probability estimate.",
  "Kelly Criterion": "Find the optimal fraction of your bankroll to wager based on your edge.",
  "Arbitrage": "Detect guaranteed-profit opportunities across books and calculate exact stakes.",
  "CLV": "Measure how sharp your bet was by comparing it to the closing line.",
  "Hold": "Calculate the sportsbook's total margin across all sides of a market.",
  "Vig": "Calculate the juice built into a market. Same as hold, different framing.",
  "Bonus Bet": "Convert a free bet or bonus to guaranteed cash using a hedge.",
  "Odds Converter": "Convert between American, decimal, fractional, and implied probability.",
  "Parlay": "Calculate combined odds and total payout for a multi-leg parlay.",
  "Prediction Market": "Convert Kalshi or Polymarket prices to standard odds formats.",
  "Point Spread": "Estimate win probability and implied moneyline from a point spread.",
  "Poisson": "Model goal/run/score distributions using the Poisson probability formula.",
  "Round Robin": "Generate all parlay combinations from a set of picks and calculate payouts.",
}

export default function CalculatorPage() {
  const [active, setActive] = useState<Calc>("No-Vig Fair Odds")

  return (
    <ProtectedRoute>
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{TITLES[active]}</h1>
        <p className="text-sm text-muted-foreground mt-1">{DESCRIPTIONS[active]}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {CALCS.map((c) => (
          <button key={c} onClick={() => setActive(c)}
            className={`px-3 py-1.5 rounded-full border text-sm font-medium transition-colors ${
              active === c
                ? "bg-foreground text-background border-foreground"
                : "text-muted-foreground border-border hover:text-foreground hover:border-foreground/40"
            }`}>
            {c} Calculator
          </button>
        ))}
      </div>

      <div>
        {active === "Implied Probability" && <ImpliedProbCalc />}
        {active === "No-Vig Fair Odds" && <NoVigCalc />}
        {active === "Expected Value" && <EVCalc />}
        {active === "Kelly Criterion" && <KellyCalc />}
        {active === "Arbitrage" && <ArbCalc />}
        {active === "CLV" && <CLVCalc />}
        {active === "Hold" && <HoldVigCalc mode="hold" />}
        {active === "Vig" && <HoldVigCalc mode="vig" />}
        {active === "Bonus Bet" && <BonusBetCalc />}
        {active === "Odds Converter" && <OddsConverterCalc />}
        {active === "Parlay" && <ParlayCalc />}
        {active === "Prediction Market" && <PredictionMarketCalc />}
        {active === "Point Spread" && <PointSpreadCalc />}
        {active === "Poisson" && <PoissonCalc />}
        {active === "Round Robin" && <RoundRobinCalc />}
      </div>
    </div>
    </ProtectedRoute>
  )
}