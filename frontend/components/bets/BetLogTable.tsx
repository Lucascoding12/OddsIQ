import { type Bet } from "@/lib/api"
import { Badge } from "@/components/ui/badge"

function formatOdds(odds: number | undefined | null) {
  if (odds == null) return "—"
  return odds > 0 ? `+${odds}` : `${odds}`
}

type Props = { bets: Bet[] }

export function BetLogTable({ bets }: Props) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b">
          <tr>
            <th className="text-left px-4 py-3 font-medium">Date</th>
            <th className="text-left px-4 py-3 font-medium">Sport</th>
            <th className="text-left px-4 py-3 font-medium">Game</th>
            <th className="text-left px-4 py-3 font-medium">Bet</th>
            <th className="text-right px-4 py-3 font-medium">Odds</th>
            <th className="text-right px-4 py-3 font-medium">Stake</th>
            <th className="text-right px-4 py-3 font-medium">Result</th>
            <th className="text-right px-4 py-3 font-medium">PnL</th>
            <th className="text-right px-4 py-3 font-medium">Closing</th>
            <th className="text-right px-4 py-3 font-medium">CLV</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {bets.map((bet) => (
            <tr key={bet.id} className="hover:bg-muted/30 transition-colors">
              <td className="px-4 py-3 text-muted-foreground">{bet.date}</td>
              <td className="px-4 py-3 text-muted-foreground text-xs">{bet.sport}</td>
              <td className="px-4 py-3">{bet.game}</td>
              <td className="px-4 py-3">{bet.betType}</td>
              <td className="px-4 py-3 text-right">{formatOdds(bet.odds)}</td>
              <td className="px-4 py-3 text-right">${bet.stake}</td>
              <td className="px-4 py-3 text-right">
                <Badge variant={bet.result === "win" ? "default" : bet.result === "loss" ? "destructive" : "secondary"}>
                  {bet.result}
                </Badge>
              </td>
              <td className="px-4 py-3 text-right font-medium font-mono">
                {bet.pnl === 0 ? "-" : `${bet.pnl > 0 ? "+" : ""}$${bet.pnl.toFixed(2)}`}
              </td>
              <td className="px-4 py-3 text-right text-muted-foreground">{formatOdds(bet.closingOdds)}</td>
              <td className="px-4 py-3 text-right font-medium text-muted-foreground">
                {!bet.clv ? "—" : `${bet.clv > 0 ? "+" : ""}${bet.clv}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
