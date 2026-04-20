const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface ControlState {
  current_status: string;
  last_run_at: string | null;
  first_failed_at: string | null;
  last_status_changed_at: string | null;
  consecutive_failures: number;
  failing_resource_count: number;
}

export interface ControlSummary {
  id: string;
  key: string;
  name: string;
  description: string | null;
  owner: string | null;
  enabled: boolean;
  connector_type: string;
  evaluator_type: string;
  current_state: ControlState | null;
}

export interface RunSummary {
  id: string;
  control_id: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  summary: string | null;
  error_message: string | null;
}

export interface Failure {
  id: string;
  resource_type: string;
  resource_identifier: string;
  details_json: Record<string, unknown> | null;
}

export interface RunDetail extends RunSummary {
  evidence_json: Record<string, unknown> | null;
  run_metadata_json: Record<string, unknown> | null;
  failures: Failure[];
}
