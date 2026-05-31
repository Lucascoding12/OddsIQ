import { type Bet } from "@/lib/api"

type Props = { bets: Bet[] }

export function ClvPanel({ bets }: Props) {
  const settled = bets.filter((b) => b.result !== "pending" && b.clv != null && b.clv !== 0)
  const avgClv = settled.length > 0
    ? settled.reduce((s, b) => s + (b.clv ?? 0), 0) / settled.length
    : 0
  const positive = settled.filter((b) => (b.clv ?? 0) > 0).length

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="font-semibold">Closing Line <span className="text-primary">Value</span> (CLV)</div>
      <p className="text-xs text-muted-foreground">
        CLV measures how much better your bet was than the closing price.
        Positive CLV over a large sample indicates you are beating the market.
        CLV is populated once a game closes and the final line is recorded.
      </p>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="rounded border px-3 py-2">
          <div className="text-xs text-muted-foreground">Avg CLV</div>
          <div className={`text-xl font-bold ${avgClv >= 0 ? "text-primary" : "text-red-400"}`}>
            {avgClv >= 0 ? "+" : ""}{avgClv.toFixed(1)}
          </div>
        </div>
        <div className="rounded border px-3 py-2">
          <div className="text-xs text-muted-foreground">Positive CLV bets</div>
          <div className="text-xl font-bold">{positive}/{settled.length}</div>
        </div>
        <div className="rounded border px-3 py-2">
          <div className="text-xs text-muted-foreground">CLV win rate</div>
          <div className="text-xl font-bold">
            {settled.length > 0 ? ((positive / settled.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
      </div>

      {settled.length === 0 ? (
        <div className="text-xs text-muted-foreground text-center py-4 border border-dashed border-border rounded-lg">
          No settled bets with CLV data yet. Log bets in the PnL tab to track your edge.
        </div>
      ) : (
        <div className="space-y-1">
          {settled.map((b) => (
            <div key={b.id} className="flex justify-between text-sm py-1 border-b last:border-0">
              <span className="text-muted-foreground">{b.game} — {b.betType}</span>
              <span className={`font-medium ${(b.clv ?? 0) > 0 ? "text-primary" : "text-red-400"}`}>
                {(b.clv ?? 0) > 0 ? "+" : ""}{b.clv} CLV
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
