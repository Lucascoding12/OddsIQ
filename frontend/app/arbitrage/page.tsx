import { ArbCalculator } from "@/components/arb/ArbCalculator"
import { ProtectedRoute } from "@/components/ProtectedRoute"

export default function ArbitragePage() {
  return (
    <ProtectedRoute>
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Arbitrage Calculator</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Enter odds from two books to find guaranteed-profit opportunities
        </p>
      </div>

      <div className="rounded-lg border p-4 bg-muted/30 text-sm space-y-1">
        <div className="font-medium">How arb betting works</div>
        <p className="text-muted-foreground">
          Arbitrage exists when the combined implied probability across books is below 100%.
          You bet both sides proportionally so you win regardless of outcome.
        </p>
      </div>

      <ArbCalculator />
    </div>
    </ProtectedRoute>
  )
}