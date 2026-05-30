import { Game } from "@/lib/mock-data"
import { Button } from "@/components/ui/button"

const CATEGORY_COLORS: Record<string, string> = {
  "American Football": "bg-orange-950 text-orange-300",
  "Basketball":        "bg-blue-950 text-blue-300",
  "Baseball":          "bg-red-950 text-red-300",
  "Hockey":            "bg-cyan-950 text-cyan-300",
  "Soccer":            "bg-green-950 text-green-300",
  "Tennis":            "bg-yellow-950 text-yellow-300",
  "Combat Sports":     "bg-purple-950 text-purple-300",
  "Cricket":           "bg-lime-950 text-lime-300",
  "Rugby":             "bg-emerald-950 text-emerald-300",
  "Golf":              "bg-teal-950 text-teal-300",
  "Motorsports":       "bg-rose-950 text-rose-300",
  "Esports":           "bg-violet-950 text-violet-300",
  "Politics & Specials": "bg-slate-800 text-slate-300",
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
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${CATEGORY_COLORS[game.category] ?? "bg-slate-800 text-slate-300"}`}>
                  {game.sport}
                </span>
              </td>
              <td className="px-4 py-3 text-right font-mono text-xs">
                <span className="text-blue-300 font-medium">{formatOdds(game.bestLine.homeMoneyline)}</span>
                {" / "}
                <span className="text-muted-foreground">{formatOdds(game.bestLine.awayMoneyline)}</span>
              </td>
              <td className="px-4 py-3 text-right font-mono text-xs">
                {game.bestLine.spread > 0 ? "+" : ""}{game.bestLine.spread}{" "}
                <span className="text-muted-foreground">({formatOdds(game.bestLine.spreadOdds)})</span>
              </td>
              <td className="px-4 py-3 text-right font-mono text-xs">
                {game.bestLine.total}{" "}
                <span className="text-muted-foreground">(O/U {formatOdds(game.bestLine.overOdds)})</span>
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
