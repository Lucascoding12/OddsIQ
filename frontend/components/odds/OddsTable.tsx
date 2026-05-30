import { Game } from "@/lib/mock-data"
import { Button } from "@/components/ui/button"

const SPORT_COLORS: Record<string, string> = {
  NFL: "bg-amber-100 text-amber-800",
  NBA: "bg-blue-100 text-blue-800",
  MLB: "bg-red-100 text-red-800",
  NHL: "bg-slate-100 text-slate-800",
}

function formatOdds(odds: number) {
  return odds > 0 ? `+${odds}` : `${odds}`
}

type Props = { games: Game[] }

export function OddsTable({ games }: Props) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b">
          <tr>
            <th className="text-left px-4 py-3 font-medium">Game</th>
            <th className="text-left px-4 py-3 font-medium">Sport</th>
            <th className="text-right px-4 py-3 font-medium">Moneyline</th>
            <th className="text-right px-4 py-3 font-medium">Spread</th>
            <th className="text-right px-4 py-3 font-medium">Total</th>
            <th className="text-right px-4 py-3 font-medium">Best Book</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y">
          {games.map((game) => (
            <tr key={game.id} className="hover:bg-muted/30 transition-colors">
              <td className="px-4 py-3 font-medium">
                {game.awayTeam} @ {game.homeTeam}
              </td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${SPORT_COLORS[game.sport]}`}>
                  {game.sport}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <span className="text-green-600 font-medium">{formatOdds(game.bestLine.homeMoneyline)}</span>
                {" / "}
                <span>{formatOdds(game.bestLine.awayMoneyline)}</span>
              </td>
              <td className="px-4 py-3 text-right">
                {game.bestLine.spread > 0 ? "+" : ""}{game.bestLine.spread}{" "}
                ({formatOdds(game.bestLine.spreadOdds)})
              </td>
              <td className="px-4 py-3 text-right">
                {game.bestLine.total} (O/U {formatOdds(game.bestLine.overOdds)})
              </td>
              <td className="px-4 py-3 text-right text-muted-foreground text-xs">
                {game.bestLine.book}
              </td>
              <td className="px-4 py-3 text-right">
                <a href={`/line-shopping?game=${game.id}`}>
                  <Button variant="outline" size="sm">
                    Compare
                  </Button>
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
