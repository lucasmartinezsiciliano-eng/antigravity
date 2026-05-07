const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://172.16.16.110:8001/api/v1";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
  return data as T;
}

export interface QuizAnswers {
  hair_texture?: string;
  hair_density?: string;
  lifestyle?: string;
  style_goal?: string;
  preferred_length?: string;
  maintenance_willingness?: string;
  style_preference?: string;
  beard?: string;
  problematic_areas?: string[];
  additional_notes?: string;
}

export interface AnalysisResult {
  analysis_id: string;
  face_shape: string;
  cranial_proportion: string;
  asymmetry_score: number;
  confidence: number;
  photos_analyzed: number;
  report: Record<string, any>;
  includes_colorimetry: boolean;
  colorimetry_report: Record<string, any> | null;
  includes_products_guide: boolean;
  products_guide: Record<string, any> | null;
  created_at: string;
  expires_at: string;
}

export const api = {
  initiate: (body: { barber_code?: string; quiz_answers?: QuizAnswers; marketing_consent?: boolean }) =>
    req<{ analysis_id: string; checkout_url: string; amount_euros: number }>(
      "/analysis/initiate",
      { method: "POST", body: JSON.stringify(body) }
    ),

  consent: (id: string, consentHash: string) =>
    req(`/analysis/${id}/consent`, {
      method: "POST",
      body: JSON.stringify({
        consented_biometric_processing: true,
        consented_special_category_data: true,
        consented_retention_90_days: true,
        consented_immediate_photo_deletion: true,
        consented_age_verification: true,
        consent_text_hash: consentHash,
      }),
    }),

  uploadPhoto: async (id: string, file: File) => {
    const fd = new FormData();
    fd.append("photos", file);
    const res = await fetch(`${BASE}/analysis/${id}/photos`, { method: "POST", body: fd });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
    return data;
  },

  uploadPhotos: async (id: string, files: File[]) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("photos", f));
    const res = await fetch(`${BASE}/analysis/${id}/photos`, { method: "POST", body: fd });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
    return data;
  },

  getResult: (id: string) => req<AnalysisResult>(`/analysis/${id}`),

  upsell: (id: string, type: "colorimetry" | "products" | "pack") =>
    req<{ checkout_url: string; amount_euros: number }>(`/analysis/${id}/upsell`, {
      method: "POST",
      body: JSON.stringify({ upsell_type: type }),
    }),

  generateVisuals: async (id: string, file: File) => {
    const fd = new FormData();
    fd.append("photo", file);
    const res = await fetch(`${BASE}/analysis/${id}/generate-visuals`, { method: "POST", body: fd });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
    return data;
  },

  getVisuals: (id: string) =>
    req<{ visuals_status: string; visuals: any[] }>(`/analysis/${id}/visuals`),

  unsubscribe: (id: string) =>
    req<{ unsubscribed: boolean }>(`/analysis/${id}/unsubscribe`, { method: "POST" }),

  /**
   * Polls payment / processing status without throwing on expected interim codes.
   * 402 → payment not yet confirmed by Stripe webhook → keep polling
   * 202 → payment confirmed, awaiting photos → redirect to /capture
   * 200 → analysis complete → redirect to /result
   */
  getAnalysisStatus: async (
    id: string,
  ): Promise<{ code: 402 | 202 | 200; result?: AnalysisResult }> => {
    const res = await fetch(`${BASE}/analysis/${id}`);
    if (res.status === 402) return { code: 402 };
    if (res.status === 202) return { code: 202 };
    if (res.ok) {
      const data = await res.json().catch(() => null);
      return { code: 200, result: data };
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  },
};
