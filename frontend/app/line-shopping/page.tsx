"use client"
import { ProtectedRoute } from "@/components/ProtectedRoute"

export default function LineShoppingPage() {
  return (
    <ProtectedRoute>
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Line Shopping</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Compare odds across all books for a single game
        </p>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-sm font-medium text-foreground">No games available</p>
          <p className="text-xs text-muted-foreground mt-1">Games will appear here once live odds are connected</p>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  )
}