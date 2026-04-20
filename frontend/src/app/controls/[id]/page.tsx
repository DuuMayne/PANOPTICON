'use client';

import { useEffect, useState, use } from 'react';
import StatusBadge from '@/components/StatusBadge';
import { apiFetch, ControlSummary, RunDetail, RunSummary } from '@/lib/api';

export default function ControlDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [control, setControl] = useState<ControlSummary | null>(null);
  const [latestRun, setLatestRun] = useState<RunDetail | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [triggering, setTriggering] = useState(false);

  const load = () => {
    apiFetch<ControlSummary>(`/controls/${id}`).then(setControl);
    apiFetch<RunDetail | null>(`/controls/${id}/runs/latest`).then(setLatestRun);
    apiFetch<RunSummary[]>(`/controls/${id}/runs?limit=20`).then(setRuns);
  };

  useEffect(load, [id]);

  const triggerRun = async () => {
    setTriggering(true);
    await apiFetch(`/controls/${id}/run`, { method: 'POST' });
    setTimeout(() => { load(); setTriggering(false); }, 2000);
  };

  if (!control) return <div className="text-center py-12 text-[var(--muted)]">Loading...</div>;

  const state = control.current_state;
  const status = state?.current_status || 'pending';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <StatusBadge status={status} />
            <span className="text-xs text-[var(--muted)] font-mono">{control.key}</span>
          </div>
          <h1 className="text-xl font-bold">{control.name}</h1>
          {control.description && <p className="text-sm text-[var(--muted)] mt-1 max-w-2xl">{control.description}</p>}
        </div>
        <button
          onClick={triggerRun}
          disabled={triggering}
          className="px-3 py-1.5 bg-[var(--accent)] text-white text-sm rounded hover:opacity-90 disabled:opacity-50"
        >
          {triggering ? 'Running...' : 'Run Now'}
        </button>
      </div>

      {/* Current state */}
      {state && (
        <div className="card">
          <h2 className="text-sm font-semibold mb-3">Current State</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-xs text-[var(--muted)]">Status</div>
              <StatusBadge status={status} />
            </div>
            <div>
              <div className="text-xs text-[var(--muted)]">Failing Resources</div>
              <div className={`font-mono ${state.failing_resource_count > 0 ? 'text-red-400' : ''}`}>
                {state.failing_resource_count}
              </div>
            </div>
            <div>
              <div className="text-xs text-[var(--muted)]">Consecutive Failures</div>
              <div className="font-mono">{state.consecutive_failures}</div>
            </div>
            <div>
              <div className="text-xs text-[var(--muted)]">Last Run</div>
              <div className="font-mono text-xs">{state.last_run_at ? new Date(state.last_run_at).toLocaleString() : 'Never'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Latest run evidence */}
      {latestRun && (
        <div className="card">
          <h2 className="text-sm font-semibold mb-2">Latest Run</h2>
          <div className="flex items-center gap-2 mb-3">
            <StatusBadge status={latestRun.status} />
            <span className="text-sm">{latestRun.summary}</span>
          </div>

          {latestRun.evidence_json && Object.keys(latestRun.evidence_json).length > 0 && (
            <div className="mb-3">
              <h3 className="text-xs font-semibold text-[var(--muted)] mb-1">Evidence</h3>
              <pre className="text-xs bg-[var(--background)] rounded p-3 overflow-x-auto">
                {JSON.stringify(latestRun.evidence_json, null, 2)}
              </pre>
            </div>
          )}

          {latestRun.failures.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-[var(--muted)] mb-1">
                Failing Resources ({latestRun.failures.length})
              </h3>
              <div className="space-y-1">
                {latestRun.failures.map((f) => (
                  <div key={f.id} className="flex items-center gap-2 text-sm bg-[var(--background)] rounded px-3 py-2">
                    <span className="text-xs text-[var(--muted)]">{f.resource_type}</span>
                    <span className="font-mono text-red-400">{f.resource_identifier}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {latestRun.error_message && (
            <div className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded text-sm text-red-400">
              {latestRun.error_message}
            </div>
          )}
        </div>
      )}

      {/* Run history */}
      {runs.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold mb-3">History ({runs.length} runs)</h2>
          <div className="space-y-1">
            {runs.map((r) => (
              <div key={r.id} className="flex items-center justify-between text-sm py-1.5 border-b border-[var(--border)] last:border-0">
                <div className="flex items-center gap-2">
                  <StatusBadge status={r.status} />
                  <span className="text-[var(--muted)] truncate max-w-md">{r.summary || '-'}</span>
                </div>
                <span className="text-xs text-[var(--muted)] font-mono shrink-0">
                  {new Date(r.started_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <a href="/" className="text-xs text-[var(--accent)] hover:underline">&larr; Back to dashboard</a>
    </div>
  );
}
