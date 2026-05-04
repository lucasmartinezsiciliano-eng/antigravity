/**
 * StyleScan API client
 * All calls to the FastAPI backend.
 */

const BASE_URL = __DEV__
  ? "http://localhost:8000/api/v1"
  : "https://api.stylescan.app/api/v1";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface QuizAnswers {
  hair_texture: "straight" | "wavy" | "curly" | "coily";
  hair_density: "thin" | "medium" | "thick";
  preferred_length: "very_short" | "short" | "medium" | "long";
  maintenance_willingness: "low" | "medium" | "high";
  style_preference: "classic" | "modern" | "trendy";
  beard: "none" | "stubble" | "short" | "full";
  problematic_areas: string[];
  additional_notes?: string;
}

export interface InitiateResponse {
  analysis_id: string;
  checkout_url: string;
  amount_euros: number;
  discount_applied: boolean;
}

export interface HaircutRecommendation {
  nombre: string;
  nombre_tecnico: string;
  nivel_estilo: string;
  nivel_mantenimiento: string;
  descripcion_favorece: string;
  como_pedirlo_al_barbero: string;
  mantenimiento_casa: string;
  frecuencia_barberia: string;
}

export interface AnalysisReport {
  resumen_facial: string;
  proporciones_craneales: string;
  cortes_recomendados: HaircutRecommendation[];
  cortes_a_evitar: string[];
  consejos_especificos: string;
}

export interface AnalysisResult {
  analysis_id: string;
  face_shape: string;
  cranial_proportion: string;
  asymmetry_score: number;
  confidence: number;
  photos_analyzed: number;
  report: AnalysisReport;
  includes_colorimetry: boolean;
  colorimetry_report: object | null;
  includes_products_guide: boolean;
  products_guide: object | null;
  created_at: string;
  expires_at: string;
}

// ─── API calls ────────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  /** Step 1: Create analysis + get Stripe checkout URL */
  initiateAnalysis: (params: {
    barber_code?: string;
    phone_hash?: string;
    quiz_answers: QuizAnswers;
    include_colorimetry?: boolean;
    include_products_guide?: boolean;
  }) =>
    request<InitiateResponse>("/analysis/initiate", {
      method: "POST",
      body: JSON.stringify(params),
    }),

  /** Step 2: Record RGPD consent */
  recordConsent: (
    analysis_id: string,
    consent: {
      consented_biometric_processing: boolean;
      consented_special_category_data: boolean;
      consented_retention_90_days: boolean;
      consented_immediate_photo_deletion: boolean;
      consented_age_verification: boolean;
      consent_text_hash: string;
      device_fingerprint_hash?: string;
    }
  ) =>
    request(`/analysis/${analysis_id}/consent`, {
      method: "POST",
      body: JSON.stringify(consent),
    }),

  /** Step 3: Upload photos for analysis */
  uploadPhotos: async (analysis_id: string, photoUris: string[]) => {
    const formData = new FormData();
    for (const uri of photoUris) {
      const filename = uri.split("/").pop() ?? "photo.jpg";
      formData.append("photos", {
        uri,
        name: filename,
        type: "image/jpeg",
      } as any);
    }

    const res = await fetch(`${BASE_URL}/analysis/${analysis_id}/photos`, {
      method: "POST",
      body: formData,
      // No Content-Type header — let fetch set multipart boundary
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail ?? `HTTP ${res.status}`);
    }

    return res.json();
  },

  /** Poll for analysis result */
  getResult: (analysis_id: string) =>
    request<AnalysisResult>(`/analysis/${analysis_id}`),

  /** RGPD: delete analysis data */
  deleteAnalysis: (analysis_id: string) =>
    request(`/analysis/${analysis_id}`, { method: "DELETE" }),
};
