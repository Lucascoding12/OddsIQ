const MOCK_LINE_MOVEMENT = [
  { game: "Chiefs vs Bills", betType: "Spread", open: -2.5, current: -3.5, book: "Pinnacle", steamFlag: true },
  { game: "Celtics vs Lakers", betType: "ML", open: -185, current: -200, book: "DraftKings", steamFlag: false },
  { game: "Yankees vs Red Sox", betType: "Total", open: 8.5, current: 9, book: "FanDuel", steamFlag: true },
]

export function LineMovementPanel() {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="font-semibold">Line Movement</div>
      <p className="text-xs text-muted-foreground">Lines that have moved significantly since open. Steam flag indicates rapid movement across multiple books (sharp money signal).</p>
      <div className="space-y-2">
        {MOCK_LINE_MOVEMENT.map((line) => (
          <div key={`${line.game}-${line.betType}`} className="flex items-center justify-between rounded border px-3 py-2 text-sm">
            <div>
              <span className="font-medium">{line.game}</span>
              <span className="text-muted-foreground ml-2">{line.betType}</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-muted-foreground">{line.open} → <span className="text-foreground font-medium">{line.current}</span></span>
              <span className="text-xs text-muted-foreground">{line.book}</span>
              {line.steamFlag && (
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-orange-100 text-orange-700">Steam</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
