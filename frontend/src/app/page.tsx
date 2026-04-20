'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import StatusBadge from '@/components/StatusBadge';
import { apiFetch, ControlSummary } from '@/lib/api';

const CONNECTOR_LABELS: Record<string, string> = {
  okta: 'Okta',
  github: 'GitHub',
  aws: 'AWS',
};

function timeAgo(iso: string | null): string {
  if (!iso) return 'Never';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function Dashboard() {
  const [controls, setControls] = useState<ControlSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch<ControlSummary[]>('/controls')
      .then(setControls)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const summary = controls.reduce(
    (acc, c) => {
      const status = c.current_state?.current_status || 'pending';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const totalFailing = controls.reduce(
    (acc, c) => acc + (c.current_state?.failing_resource_count || 0), 0
  );

  if (loading) return <div className="text-center py-12 text-[var(--muted)]">Loading controls...</div>;
  if (error) return <div className="text-center py-12 text-[var(--danger)]">Error: {error}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Control Status</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card">
          <div className="text-xs text-[var(--muted)] mb-1">Total Controls</div>
          <div className="text-2xl font-bold">{controls.length}</div>
        </div>
        <div className="card">
          <div className="text-xs text-[var(--muted)] mb-1">Passing</div>
          <div className="text-2xl font-bold text-emerald-400">{summary.pass || 0}</div>
        </div>
        <div className="card">
          <div className="text-xs text-[var(--muted)] mb-1">Failing</div>
          <div className={`text-2xl font-bold ${(summary.fail || 0) > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {summary.fail || 0}
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-[var(--muted)] mb-1">Failing Resources</div>
          <div className={`text-2xl font-bold ${totalFailing > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {totalFailing}
          </div>
        </div>
      </div>

      {/* Control list */}
      <div className="space-y-2">
        {controls.map((c) => {
          const state = c.current_state;
          const status = state?.current_status || 'pending';
          return (
            <Link
              key={c.id}
              href={`/controls/${c.id}`}
              className="card flex items-center justify-between hover:border-[var(--accent)] transition-colors cursor-pointer block"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <StatusBadge status={status} />
                  <span className="font-medium text-sm truncate">{c.name}</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-[var(--muted)]">
                  <span>{CONNECTOR_LABELS[c.connector_type] || c.connector_type}</span>
                  {c.owner && <span>{c.owner}</span>}
                </div>
              </div>
              <div className="text-right shrink-0 ml-4">
                <div className="text-xs text-[var(--muted)]">
                  {timeAgo(state?.last_run_at || null)}
                </div>
                {status === 'fail' && state && (
                  <div className="text-xs text-red-400 mt-0.5">
                    {state.failing_resource_count} failing
                    {state.consecutive_failures > 1 && ` (${state.consecutive_failures}x)`}
                  </div>
                )}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
