"use client"

import { ProtectedRoute } from "@/components/ProtectedRoute"
import { AlertList } from "@/components/alerts/AlertList"
import { AlertForm } from "@/components/alerts/AlertForm"
import { useAlerts } from "@/lib/hooks"
import { createAlert, deleteAlert, type AlertCreate } from "@/lib/api"

export default function AlertsPage() {
  const { data, isLoading, mutate } = useAlerts()
  const alerts = data ?? []

  async function handleCreate(body: AlertCreate) {
    const created = await createAlert(body)
    await mutate((prev) => [created, ...(prev ?? [])], { revalidate: false })
  }

  async function handleDelete(id: number) {
    await deleteAlert(id)
    await mutate((prev) => (prev ?? []).filter((a) => a.id !== id), { revalidate: false })
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Price <span className="text-primary">Alerts</span></h1>
          <p className="mt-1 text-sm text-muted-foreground">Get notified when a line hits your target</p>
        </div>
        {isLoading && !data ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }, (_, i) => (
              <div key={i} className="skeleton h-14 w-full" />
            ))}
          </div>
        ) : (
          <AlertList alerts={alerts} onDelete={handleDelete} />
        )}
        <AlertForm onSubmit={handleCreate} />
      </div>
    </ProtectedRoute>
  )
}
