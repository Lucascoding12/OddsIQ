import { BookOdds } from "@/lib/mock-data"

function formatOdds(odds: number) {
  return odds > 0 ? `+${odds}` : `${odds}`
}

type Props = { books: BookOdds[] }

export function BookComparison({ books }: Props) {
  const bestML = Math.max(...books.map((b) => b.homeMoneyline))
  const bestSpreadOdds = Math.max(...books.map((b) => b.spreadOdds))
  const bestOverOdds = Math.max(...books.map((b) => b.overOdds))

  return (
    <div className="rounded-lg border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b">
          <tr>
            <th className="text-left px-4 py-3 font-medium">Book</th>
            <th className="text-right px-4 py-3 font-medium">Home ML</th>
            <th className="text-right px-4 py-3 font-medium">Away ML</th>
            <th className="text-right px-4 py-3 font-medium">Spread</th>
            <th className="text-right px-4 py-3 font-medium">Spread Odds</th>
            <th className="text-right px-4 py-3 font-medium">Total</th>
            <th className="text-right px-4 py-3 font-medium">Over</th>
            <th className="text-right px-4 py-3 font-medium">Under</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {books.map((b) => (
            <tr key={b.book} className="hover:bg-muted/30 transition-colors">
              <td className="px-4 py-3 font-medium">{b.book}</td>
              <td className={`px-4 py-3 text-right font-medium ${b.homeMoneyline === bestML ? "text-green-600" : ""}`}>
                {formatOdds(b.homeMoneyline)}
              </td>
              <td className="px-4 py-3 text-right">{formatOdds(b.awayMoneyline)}</td>
              <td className="px-4 py-3 text-right">{b.spread > 0 ? "+" : ""}{b.spread}</td>
              <td className={`px-4 py-3 text-right ${b.spreadOdds === bestSpreadOdds ? "text-green-600 font-medium" : ""}`}>
                {formatOdds(b.spreadOdds)}
              </td>
              <td className="px-4 py-3 text-right">{b.total}</td>
              <td className={`px-4 py-3 text-right ${b.overOdds === bestOverOdds ? "text-green-600 font-medium" : ""}`}>
                {formatOdds(b.overOdds)}
              </td>
              <td className="px-4 py-3 text-right">{formatOdds(b.underOdds)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-4 py-2 bg-muted/30 text-xs text-muted-foreground">
        Green = best available line for that market
      </div>
    </div>
  )
}
