const KEYS = {
  quiz: "ss_quiz",
  analysisId: "ss_analysis_id",
  barberCode: "ss_barber_code",
  checkoutUrl: "ss_checkout_url",
  consentState: "ss_consent",
  email: "ss_email",
  phone: "ss_phone",
};

export const storage = {
  // Clears every key tied to a single analysis run. `barberCode` is reusable across
  // analyses so it is intentionally preserved.
  clearAnalysisData: () => {
    try {
      localStorage.removeItem(KEYS.analysisId);
      localStorage.removeItem(KEYS.checkoutUrl);
      localStorage.removeItem(KEYS.quiz);
      localStorage.removeItem(KEYS.consentState);
    } catch {}
  },
  saveQuiz: (answers: Record<string, any>) => {
    try { localStorage.setItem(KEYS.quiz, JSON.stringify(answers)); } catch {}
  },
  getQuiz: (): Record<string, any> => {
    try { return JSON.parse(localStorage.getItem(KEYS.quiz) ?? "{}"); } catch { return {}; }
  },
  saveAnalysisId: (id: string) => {
    // A new analysis is starting — drop stale data from any previous run first.
    // Also clear quiz so old answers don't bleed into a new analysis (reported bug).
    try {
      localStorage.removeItem(KEYS.checkoutUrl);
      localStorage.removeItem(KEYS.consentState);
      localStorage.removeItem(KEYS.quiz);
    } catch {}
    try { localStorage.setItem(KEYS.analysisId, id); } catch {}
  },
  getAnalysisId: (): string | null => {
    try { return localStorage.getItem(KEYS.analysisId); } catch { return null; }
  },
  clearAnalysisId: () => {
    try { localStorage.removeItem(KEYS.analysisId); } catch {}
  },
  saveBarberCode: (code: string) => {
    try { localStorage.setItem(KEYS.barberCode, code); } catch {}
  },
  getBarberCode: (): string | null => {
    try { return localStorage.getItem(KEYS.barberCode); } catch { return null; }
  },
  clearBarberCode: () => {
    try { localStorage.removeItem(KEYS.barberCode); } catch {}
  },
  saveCheckoutUrl: (url: string) => {
    try { localStorage.setItem(KEYS.checkoutUrl, url); } catch {}
  },
  getCheckoutUrl: (): string | null => {
    try { return localStorage.getItem(KEYS.checkoutUrl); } catch { return null; }
  },
  clearCheckoutUrl: () => {
    try { localStorage.removeItem(KEYS.checkoutUrl); } catch {}
  },
  saveConsentState: (state: Record<string, boolean>) => {
    try { localStorage.setItem(KEYS.consentState, JSON.stringify(state)); } catch {}
  },
  getConsentState: (): Record<string, boolean> => {
    try { return JSON.parse(localStorage.getItem(KEYS.consentState) ?? "{}"); } catch { return {}; }
  },
  saveEmail: (email: string) => {
    try { localStorage.setItem(KEYS.email, email); } catch {}
  },
  getEmail: (): string | null => {
    try { return localStorage.getItem(KEYS.email); } catch { return null; }
  },
  savePhone: (phone: string) => {
    try { localStorage.setItem(KEYS.phone, phone); } catch {}
  },
  getPhone: (): string | null => {
    try { return localStorage.getItem(KEYS.phone); } catch { return null; }
  },
};
