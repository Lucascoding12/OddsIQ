import { ClvPanel } from "@/components/sharp/ClvPanel"
import { LineMovementPanel } from "@/components/sharp/LineMovementPanel"
import { MOCK_BETS } from "@/lib/mock-data"

export default function SharpPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Sharp Metrics</h1>
        <p className="text-sm text-muted-foreground mt-1">Tools used by professional bettors to evaluate edge</p>
      </div>
      <ClvPanel bets={MOCK_BETS} />
      <LineMovementPanel />
    </div>
  )
}
