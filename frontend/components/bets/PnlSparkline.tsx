import { type Bet } from "@/lib/api"

type Props = { bets: Bet[] }

const W = 600
const H = 140
const PAD = 8

/**
 * Cumulative PnL over settled bets as a dependency-free inline SVG.
 * Green when the running total ends positive, red when negative.
 */
export function PnlSparkline({ bets }: Props) {
  const settled = bets
    .filter((b) => b.result !== "pending")
    .sort((a, b) => a.date.localeCompare(b.date) || a.id - b.id)

  if (settled.length < 2) return null

  const values = [0]
  for (const bet of settled) values.push(values[values.length - 1] + bet.pnl)

  const min = Math.min(0, ...values)
  const max = Math.max(0, ...values)
  const span = max - min || 1

  const x = (i: number) => PAD + (i / (values.length - 1)) * (W - PAD * 2)
  const y = (v: number) => PAD + ((max - v) / span) * (H - PAD * 2)

  const linePath = values.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ")
  const areaPath = `${linePath} L${x(values.length - 1).toFixed(1)},${y(0).toFixed(1)} L${x(0).toFixed(1)},${y(0).toFixed(1)} Z`

  const final = values[values.length - 1]
  const stroke = final >= 0 ? "#34d399" : "#f87171"
  const fill = final >= 0 ? "rgba(52, 211, 153, 0.12)" : "rgba(248, 113, 113, 0.12)"

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Cumulative PnL
        </span>
        <span className={`font-mono text-sm font-semibold ${final >= 0 ? "text-emerald-300" : "text-red-400"}`}>
          {final >= 0 ? "+" : "-"}${Math.abs(final).toFixed(2)}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        className="h-28 w-full"
        role="img"
        aria-label={`Cumulative profit and loss across ${settled.length} settled bets`}
      >
        <line
          x1={PAD} x2={W - PAD} y1={y(0)} y2={y(0)}
          stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" strokeWidth="1"
        />
        <path d={areaPath} fill={fill} />
        <path d={linePath} fill="none" stroke={stroke} strokeWidth="2" strokeLinejoin="round" />
        <circle cx={x(values.length - 1)} cy={y(final)} r="3" fill={stroke} />
      </svg>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground/60">
        <span>{settled[0].date}</span>
        <span>{settled[settled.length - 1].date}</span>
      </div>
    </div>
  )
}
