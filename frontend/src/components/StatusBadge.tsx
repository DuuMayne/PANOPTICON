const STATUS_STYLES: Record<string, string> = {
  pass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  fail: 'bg-red-500/20 text-red-400 border-red-500/30',
  error: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  pending: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

export default function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.pending;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded border ${style}`}>
      {status.toUpperCase()}
    </span>
  );
}
