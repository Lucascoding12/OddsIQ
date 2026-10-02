import { type Bet } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { formatOdds } from "@/lib/format"

type Props = { bets: Bet[]; loading?: boolean }

export function BetLogTable({ bets, loading = false }: Props) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="border-b bg-muted/50">
          <tr>
            <th className="px-4 py-3 text-left font-medium">Date</th>
            <th className="px-4 py-3 text-left font-medium">Sport</th>
            <th className="px-4 py-3 text-left font-medium">Game</th>
            <th className="px-4 py-3 text-left font-medium">Bet</th>
            <th className="px-4 py-3 text-right font-medium">Odds</th>
            <th className="px-4 py-3 text-right font-medium">Stake</th>
            <th className="px-4 py-3 text-right font-medium">Result</th>
            <th className="px-4 py-3 text-right font-medium">PnL</th>
            <th className="px-4 py-3 text-right font-medium">Closing</th>
            <th className="px-4 py-3 text-right font-medium">CLV</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {bets.length === 0 && (
            <tr>
              <td colSpan={10} className="px-4 py-12 text-center text-sm text-muted-foreground">
                {loading ? (
                  <span className="animate-pulse">Loading bets…</span>
                ) : (
                  <>
                    <div className="font-medium">No bets logged yet</div>
                    <div className="mt-1 text-xs">Log your first bet below to start tracking PnL and CLV.</div>
                  </>
                )}
              </td>
            </tr>
          )}
          {bets.map((bet) => (
            <tr key={bet.id} className="transition-colors hover:bg-muted/30">
              <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{bet.date}</td>
              <td className="px-4 py-3 text-xs text-muted-foreground">{bet.sport}</td>
              <td className="px-4 py-3">{bet.game}</td>
              <td className="px-4 py-3">{bet.betType}</td>
              <td className="px-4 py-3 text-right font-mono">{formatOdds(bet.odds)}</td>
              <td className="px-4 py-3 text-right font-mono">${bet.stake}</td>
              <td className="px-4 py-3 text-right">
                <Badge variant={bet.result === "win" ? "default" : bet.result === "loss" ? "destructive" : "secondary"}>
                  {bet.result}
                </Badge>
              </td>
              <td
                className={`px-4 py-3 text-right font-mono font-medium ${
                  bet.pnl > 0 ? "text-emerald-300" : bet.pnl < 0 ? "text-red-400" : "text-muted-foreground"
                }`}
              >
                {bet.pnl === 0 ? "—" : `${bet.pnl > 0 ? "+" : "-"}$${Math.abs(bet.pnl).toFixed(2)}`}
              </td>
              <td className="px-4 py-3 text-right font-mono text-muted-foreground">{formatOdds(bet.closingOdds)}</td>
              <td className="px-4 py-3 text-right font-mono font-medium text-muted-foreground">
                {!bet.clv ? "—" : `${bet.clv > 0 ? "+" : ""}${bet.clv}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
