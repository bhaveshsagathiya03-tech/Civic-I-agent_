export const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.DEV ? 'http://localhost:8000' : '');
export type Issue = {
  id: number; public_id: string; category: 'pothole' | 'garbage_accumulation' | null; ai_category?: string | null; verified_category?: string | null; classification_source?: string;
  declared_category?: string | null; description?: string | null; latitude: number; longitude: number;
  location_label?: string | null; image_url: string; annotated_image_url?: string | null;
  detection_confidence?: number | null; detection_status: string; detection_payload?: any;
  priority_score?: number | null; priority_level: string; priority_breakdown?: any;
  verification_status: string; status: string; duplicate_candidates?: any[];
  created_at: string; updated_at: string;
};
export type Overview = { total:number; potholes:number; garbage:number; critical:number; high:number; medium:number; low:number; awaiting_review:number; resolved:number; model_status:string };

function authHeaders() {
  const token = sessionStorage.getItem('civic_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  Object.entries(authHeaders()).forEach(([k,v]) => headers.set(k,v));
  const isForm = init.body instanceof FormData;
  if (!isForm && init.body && !headers.has('Content-Type')) headers.set('Content-Type','application/json');
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}
