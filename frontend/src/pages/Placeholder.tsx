export function Placeholder({ title, lot }: { title: string; lot: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-surface p-8 text-center">
      <h1 className="mb-2 text-lg font-semibold">{title}</h1>
      <p className="text-sm text-text-muted">À construire — {lot} (voir FRONTEND_PLAN.md)</p>
    </div>
  )
}
