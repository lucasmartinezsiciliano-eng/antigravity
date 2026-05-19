const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function extractDetail(detail: unknown, fallback: string): string {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (typeof detail === "object") {
    const d = detail as Record<string, unknown>;
    if (typeof d.message === "string") return d.message;
    if (Array.isArray(d)) return (d as {msg?: string}[]).map((e) => e.msg ?? JSON.stringify(e)).join(" | ");
    return JSON.stringify(detail);
  }
  return String(detail);
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "bypass-tunnel-reminder": "true", ...init?.headers },
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) throw new Error(extractDetail(data.detail, `HTTP ${res.status}`));
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
  includes_seasonal: boolean;
  seasonal_report: Record<string, any> | null;
  created_at: string;
  expires_at: string;
}

export const api = {
  initiate: (body: { barber_code?: string; quiz_answers?: QuizAnswers; marketing_consent?: boolean; include_colorimetry?: boolean; include_products_guide?: boolean }) =>
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
    if (!res.ok) throw new Error(extractDetail(data.detail, `HTTP ${res.status}`));
    return data;
  },

  uploadPhotos: async (id: string, files: File[]) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("photos", f));
    const res = await fetch(`${BASE}/analysis/${id}/photos`, { method: "POST", body: fd });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(extractDetail(data.detail, `HTTP ${res.status}`));
    return data;
  },

  getResult: (id: string) => req<AnalysisResult>(`/analysis/${id}`),

  upsell: (id: string, type: "colorimetry" | "products" | "pack" | "seasonal") =>
    req<{ checkout_url: string; amount_euros: number }>(`/analysis/${id}/upsell`, {
      method: "POST",
      body: JSON.stringify({ upsell_type: type }),
    }),

  generateVisuals: async (id: string, file: File, profileFile?: File) => {
    const fd = new FormData();
    fd.append("photo", file);
    if (profileFile) fd.append("profile_photo", profileFile);
    const res = await fetch(`${BASE}/analysis/${id}/generate-visuals`, { method: "POST", body: fd });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(extractDetail(data.detail, `HTTP ${res.status}`));
    return data;
  },

  getVisuals: (id: string) =>
    req<{ visuals_status: string; visuals: any[] }>(`/analysis/${id}/visuals`),

  unsubscribe: (id: string) =>
    req<{ unsubscribed: boolean }>(`/analysis/${id}/unsubscribe`, { method: "POST" }),

  getReferences: (id: string) =>
    req<{
      face_shape: string;
      cuts: Array<{
        cut_name_en: string;
        cut_name_es: string;
        references: Array<{
          image_url: string | null;
          account: string;
          post_url: string;
          face_shape: string;
          cut_name_es: string;
          why_this_works: string;
          photo_quality: number;
        }>;
      }>;
      total_refs: number;
    }>(`/analysis/${id}/references`),

  /**
   * Polls payment / processing status without throwing on expected interim codes.
   * 402 → payment not yet confirmed by Stripe webhook → keep polling
   * 202 → payment confirmed; sub-state ('paid' awaits photos, 'processing' is in-flight)
   * 200 → analysis complete → redirect to /result
   * 410 → analysis was deleted (RGPD)
   */
  getAnalysisStatus: async (
    id: string,
  ): Promise<{
    code: 402 | 202 | 200 | 410;
    result?: AnalysisResult;
    subState?: "paid" | "processing";
  }> => {
    const res = await fetch(`${BASE}/analysis/${id}`, {
      headers: { "bypass-tunnel-reminder": "true" },
    });
    if (res.status === 402) return { code: 402 };
    if (res.status === 202) {
      const data = await res.json().catch(() => ({}));
      const detail: string = typeof data?.detail === "string" ? data.detail : "";
      // Backend distinguishes via the 202 detail message:
      //  - 'paid'       → "Las fotos están siendo procesadas."   (no photos yet)
      //  - 'processing' → "El análisis está en progreso."
      const subState: "paid" | "processing" =
        detail.toLowerCase().includes("progreso") ? "processing" : "paid";
      return { code: 202, subState };
    }
    if (res.status === 410) return { code: 410 };
    if (res.ok) {
      const data = await res.json().catch(() => null);
      return { code: 200, result: data };
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  },

  // ============================================================================
  // BARBER GAMIFICATION API
  // ============================================================================

  // Contract signing
  signBarberContract: (barber_id: string) =>
    req<{ message: string; signed_at: string }>(`/barbers/${barber_id}/sign-contract`, {
      method: "POST",
      body: JSON.stringify({ contract_version: "1.0" }),
    }),

  // Barber Dashboard
  getBarberDashboard: (barber_id: string) =>
    req<{
      barber_id: string;
      name: string;
      barbershop_name: string;
      promo_code: string;
      total_uses: number;
      total_earned_euros: number;
      total_paid_out_euros: number;
      pending_payout_euros: number;
      is_active: boolean;
      recent_uses: Array<{ date: string; earned_euros: number }>;
    }>(`/barbers/${barber_id}/dashboard`),

  // Reference Photos
  getBarberReferencePhotos: (barber_id: string) =>
    req<
      Array<{
        id: string;
        haircut_type: string;
        photo_angle: string;
        cloudinary_url: string;
        validation_status: string;
        quality_score: number | null;
        created_at: string;
      }>
    >(`/barbers/${barber_id}/reference-photos`),

  uploadReferencePhoto: async (
    barber_id: string,
    file: File,
    haircut_type: string,
    photo_angle: string,
  ) => {
    const params = new URLSearchParams({
      haircut_type,
      photo_angle,
    });
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(
      `${BASE}/barbers/${barber_id}/reference-photos?${params}`,
      { method: "POST", body: fd },
    );
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new Error(extractDetail(data.detail, `HTTP ${res.status}`));
    return data;
  },

  deleteReferencePhoto: (barber_id: string, photo_id: string) =>
    req<{ message: string }>(
      `/barbers/${barber_id}/reference-photos/${photo_id}`,
      { method: "DELETE" },
    ),

  // Leaderboard
  getLeaderboard: (
    period: "week" | "month" | "all_time" = "all_time",
    city_filter?: string,
    limit: number = 50,
    offset: number = 0,
  ) => {
    const params = new URLSearchParams({
      period,
      limit: String(limit),
      offset: String(offset),
    });
    if (city_filter) params.append("city_filter", city_filter);
    return req<
      Array<{
        rank: number;
        barber_id: string;
        barber_name: string;
        barbershop_name: string;
        city: string;
        clients_this_period: number;
        clients_all_time: number;
        current_tier: string;
        instagram_handle?: string;
      }>
    >(`/leaderboard?${params}`);
  },

  getBarberLeaderboardStats: (barber_id: string) =>
    req<{
      barber_id: string;
      name: string;
      city: string;
      clients_all_time: number;
      clients_this_week: number;
      clients_this_month: number;
      all_time_ranking_position: number | null;
      week_ranking_position: number | null;
      current_tier: string;
      reference_photos_count: number;
      reference_photos_validated: number;
    }>(`/leaderboard/stats/${barber_id}`),

  // Parental Consent
  authorizeParentalConsent: (token: string) =>
    req<{
      status: string;
      message: string;
      request_id: string;
    }>(`/parental-consent/authorize?token=${token}`),

  getParentalConsentStatus: (token: string) =>
    req<{
      request_id: string;
      status: string;
      is_authorized: boolean;
      token_expires_at: string;
    }>(`/parental-consent/${token}/status`),

  // Telegram
  connectTelegram: (barber_id: string, data: {
    telegram_user_id: number;
    telegram_chat_id: number;
    telegram_username?: string;
    first_name?: string;
    last_name?: string;
  }) =>
    req<{ status: string; message: string }>(
      `/barbers/${barber_id}/telegram/connect`,
      { method: "POST", body: JSON.stringify(data) },
    ),

  updateTelegramPreferences: (
    barber_id: string,
    preferences: {
      notifications_enabled: boolean;
      notify_on_new_analysis: boolean;
      notify_on_ranking_change: boolean;
      notify_on_weekly_summary: boolean;
      language_code: string;
    },
  ) =>
    req<{ status: string; message: string }>(
      `/barbers/${barber_id}/telegram/preferences`,
      { method: "PUT", body: JSON.stringify(preferences) },
    ),
};
