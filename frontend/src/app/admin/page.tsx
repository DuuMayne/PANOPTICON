'use client';

import { useEffect, useState } from 'react';
import StatusBadge from '@/components/StatusBadge';
import { apiFetch } from '@/lib/api';

interface Connector {
  connector_type: string;
  required_env: string[];
  configured: boolean;
  has_mock_data: boolean;
}

interface Evaluator {
  evaluator_type: string;
  class_name: string;
  description: string;
}

interface ControlDetail {
  id: string;
  key: string;
  name: string;
  description: string | null;
  owner: string | null;
  enabled: boolean;
  connector_type: string;
  evaluator_type: string;
  config_json: Record<string, unknown>;
  cadence_seconds: number;
  current_state: { current_status: string } | null;
}

interface TestResult {
  connector_type: string;
  success: boolean;
  message: string;
  using_mock: boolean;
}

const CADENCE_OPTIONS = [
  { label: '1 min', value: 60 },
  { label: '5 min', value: 300 },
  { label: '15 min', value: 900 },
  { label: '1 hr', value: 3600 },
  { label: '6 hr', value: 21600 },
  { label: '12 hr', value: 43200 },
  { label: '24 hr', value: 86400 },
];

function formatCadence(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}h`;
  return `${Math.round(seconds / 86400)}d`;
}

export default function AdminPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [evaluators, setEvaluators] = useState<Evaluator[]>([]);
  const [controls, setControls] = useState<ControlDetail[]>([]);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});

  // New control form
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    key: '', name: '', description: '', owner: '',
    connector_type: '', evaluator_type: '',
    config_json: '{}', cadence_seconds: 21600, enabled: true,
  });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  // Edit control
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Record<string, unknown>>({});

  const load = () => {
    apiFetch<Connector[]>('/connectors').then(setConnectors);
    apiFetch<Evaluator[]>('/evaluators').then(setEvaluators);
    apiFetch<ControlDetail[]>('/controls').then(setControls);
  };

  useEffect(load, []);

  const testConnector = async (connectorType: string) => {
    setTesting((t) => ({ ...t, [connectorType]: true }));
    try {
      const result = await apiFetch<TestResult>(`/connectors/${connectorType}/test`, { method: 'POST' });
      setTestResults((r) => ({ ...r, [connectorType]: result }));
    } catch {
      setTestResults((r) => ({ ...r, [connectorType]: { connector_type: connectorType, success: false, message: 'Request failed', using_mock: false } }));
    }
    setTesting((t) => ({ ...t, [connectorType]: false }));
  };

  const createControl = async () => {
    setFormError('');
    setSaving(true);
    try {
      let configObj = {};
      try { configObj = JSON.parse(form.config_json); } catch { setFormError('Invalid JSON in config'); setSaving(false); return; }
      await apiFetch('/controls', {
        method: 'POST',
        body: JSON.stringify({ ...form, config_json: configObj }),
      });
      setShowForm(false);
      setForm({ key: '', name: '', description: '', owner: '', connector_type: '', evaluator_type: '', config_json: '{}', cadence_seconds: 21600, enabled: true });
      load();
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : 'Failed to create control');
    }
    setSaving(false);
  };

  const startEdit = (control: ControlDetail) => {
    setEditingId(control.id);
    setEditForm({
      name: control.name,
      description: control.description || '',
      owner: control.owner || '',
      connector_type: control.connector_type,
      evaluator_type: control.evaluator_type,
      config_json: JSON.stringify(control.config_json, null, 2),
      cadence_seconds: control.cadence_seconds,
      enabled: control.enabled,
    });
  };

  const saveEdit = async (controlId: string) => {
    try {
      let configObj = {};
      try { configObj = JSON.parse(editForm.config_json as string); } catch { return; }
      await apiFetch(`/controls/${controlId}`, {
        method: 'PUT',
        body: JSON.stringify({ ...editForm, config_json: configObj }),
      });
      setEditingId(null);
      load();
    } catch { /* ignore */ }
  };

  const deleteControl = async (controlId: string, key: string) => {
    if (!confirm(`Delete control "${key}" and all its run history?`)) return;
    await apiFetch(`/controls/${controlId}`, { method: 'DELETE' });
    load();
  };

  const toggleEnabled = async (control: ControlDetail) => {
    await apiFetch(`/controls/${control.id}`, {
      method: 'PUT',
      body: JSON.stringify({ enabled: !control.enabled }),
    });
    load();
  };

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-bold">Admin</h1>

      {/* ===== CONNECTORS ===== */}
      <section>
        <h2 className="text-sm font-semibold text-[var(--muted)] uppercase tracking-wider mb-3">Connectors</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {connectors.map((c) => {
            const result = testResults[c.connector_type];
            return (
              <div key={c.connector_type} className="card">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm">{c.connector_type}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${c.configured ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                    {c.configured ? 'Configured' : 'Mock'}
                  </span>
                </div>
                <div className="text-xs text-[var(--muted)] mb-2">
                  Requires: {c.required_env.join(', ') || 'nothing'}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => testConnector(c.connector_type)}
                    disabled={testing[c.connector_type]}
                    className="text-xs px-2 py-1 bg-[var(--accent)] text-white rounded hover:opacity-90 disabled:opacity-50"
                  >
                    {testing[c.connector_type] ? 'Testing...' : 'Test Connection'}
                  </button>
                  {result && (
                    <span className={`text-xs ${result.success ? 'text-emerald-400' : 'text-red-400'}`}>
                      {result.message}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ===== EVALUATORS ===== */}
      <section>
        <h2 className="text-sm font-semibold text-[var(--muted)] uppercase tracking-wider mb-3">Available Evaluators</h2>
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left p-3 text-xs text-[var(--muted)]">Type Key</th>
                <th className="text-left p-3 text-xs text-[var(--muted)]">Description</th>
              </tr>
            </thead>
            <tbody>
              {evaluators.map((e) => (
                <tr key={e.evaluator_type} className="border-b border-[var(--border)] last:border-0">
                  <td className="p-3 font-mono text-xs text-[var(--accent)]">{e.evaluator_type}</td>
                  <td className="p-3 text-xs text-[var(--muted)]">{e.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ===== CONTROLS ===== */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-[var(--muted)] uppercase tracking-wider">Controls</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="text-xs px-3 py-1.5 bg-[var(--accent)] text-white rounded hover:opacity-90"
          >
            {showForm ? 'Cancel' : '+ New Control'}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="card mb-4 space-y-3">
            <h3 className="text-sm font-semibold">New Control</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-[var(--muted)] block mb-1">Key *</label>
                <input className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm" placeholder="e.g., my_control"
                  value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })} />
              </div>
              <div>
                <label className="text-xs text-[var(--muted)] block mb-1">Name *</label>
                <input className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm" placeholder="Human-readable name"
                  value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-[var(--muted)] block mb-1">Description</label>
                <input className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm" placeholder="What this control checks"
                  value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <div>
                <label className="text-xs text-[var(--muted)] block mb-1">Connector Type *</label>
                <select className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                  value={form.connector_type} onChange={(e) => setForm({ ...form, connector_type: e.target.value })}>
                  <option value="">Select connector...</option>
                  {connectors.map((c) => <option key={c.connector_type} value={c.connector_type}>{c.connector_type}{!c.configured ? ' (mock)' : ''}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-[var(--muted)] block mb-1">Evaluator Type *</label>
                <select className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                  value={form.evaluator_type} onChange={(e) => setForm({ ...form, evaluator_type: e.target.value })}>
                  <option value="">Select evaluator...</option>
                  {evaluators.map((e) => <option key={e.evaluator_type} value={e.evaluator_type}>{e.evaluator_type}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-[var(--muted)] block mb-1">Owner</label>
                <input className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm" placeholder="Team or person"
                  value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} />
              </div>
              <div>
                <label className="text-xs text-[var(--muted)] block mb-1">Cadence</label>
                <select className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                  value={form.cadence_seconds} onChange={(e) => setForm({ ...form, cadence_seconds: parseInt(e.target.value) })}>
                  {CADENCE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-[var(--muted)] block mb-1">Config JSON</label>
                <textarea className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm font-mono" rows={3}
                  placeholder='{"critical_repos": ["org/repo"]}'
                  value={form.config_json} onChange={(e) => setForm({ ...form, config_json: e.target.value })} />
              </div>
            </div>
            {formError && <div className="text-xs text-red-400">{formError}</div>}
            <button
              onClick={createControl}
              disabled={saving || !form.key || !form.name || !form.connector_type || !form.evaluator_type}
              className="text-xs px-3 py-1.5 bg-emerald-600 text-white rounded hover:opacity-90 disabled:opacity-50"
            >
              {saving ? 'Creating...' : 'Create Control'}
            </button>
          </div>
        )}

        {/* Controls table */}
        <div className="space-y-2">
          {controls.map((c) => (
            <div key={c.id} className="card">
              {editingId === c.id ? (
                /* Edit mode */
                <div className="space-y-3">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-[var(--muted)] block mb-1">Name</label>
                      <input className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                        value={editForm.name as string} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} />
                    </div>
                    <div>
                      <label className="text-xs text-[var(--muted)] block mb-1">Owner</label>
                      <input className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                        value={editForm.owner as string} onChange={(e) => setEditForm({ ...editForm, owner: e.target.value })} />
                    </div>
                    <div>
                      <label className="text-xs text-[var(--muted)] block mb-1">Connector</label>
                      <select className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                        value={editForm.connector_type as string} onChange={(e) => setEditForm({ ...editForm, connector_type: e.target.value })}>
                        {connectors.map((cn) => <option key={cn.connector_type} value={cn.connector_type}>{cn.connector_type}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-[var(--muted)] block mb-1">Evaluator</label>
                      <select className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                        value={editForm.evaluator_type as string} onChange={(e) => setEditForm({ ...editForm, evaluator_type: e.target.value })}>
                        {evaluators.map((ev) => <option key={ev.evaluator_type} value={ev.evaluator_type}>{ev.evaluator_type}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-[var(--muted)] block mb-1">Cadence</label>
                      <select className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm"
                        value={editForm.cadence_seconds as number} onChange={(e) => setEditForm({ ...editForm, cadence_seconds: parseInt(e.target.value) })}>
                        {CADENCE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </div>
                    <div className="md:col-span-2">
                      <label className="text-xs text-[var(--muted)] block mb-1">Config JSON</label>
                      <textarea className="w-full bg-[var(--background)] border border-[var(--border)] rounded px-3 py-1.5 text-sm font-mono" rows={3}
                        value={editForm.config_json as string} onChange={(e) => setEditForm({ ...editForm, config_json: e.target.value })} />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => saveEdit(c.id)} className="text-xs px-3 py-1.5 bg-emerald-600 text-white rounded hover:opacity-90">Save</button>
                    <button onClick={() => setEditingId(null)} className="text-xs px-3 py-1.5 bg-[var(--border)] text-[var(--foreground)] rounded hover:opacity-90">Cancel</button>
                  </div>
                </div>
              ) : (
                /* View mode */
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <StatusBadge status={c.current_state?.current_status || 'pending'} />
                      <span className="font-medium text-sm">{c.name}</span>
                      <span className="font-mono text-xs text-[var(--muted)]">{c.key}</span>
                      {!c.enabled && <span className="text-xs px-1.5 py-0.5 rounded bg-slate-500/20 text-slate-400">Disabled</span>}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-[var(--muted)]">
                      <span>{c.connector_type}</span>
                      <span>{c.evaluator_type}</span>
                      <span>{formatCadence(c.cadence_seconds)}</span>
                      {c.owner && <span>{c.owner}</span>}
                    </div>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button onClick={() => toggleEnabled(c)}
                      className={`text-xs px-2 py-1 rounded ${c.enabled ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'}`}>
                      {c.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button onClick={() => startEdit(c)}
                      className="text-xs px-2 py-1 bg-[var(--border)] text-[var(--foreground)] rounded hover:opacity-80">
                      Edit
                    </button>
                    <button onClick={() => deleteControl(c.id, c.key)}
                      className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30">
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
