const KEYS = {
  quiz: "ss_quiz",
  analysisId: "ss_analysis_id",
  barberCode: "ss_barber_code",
  checkoutUrl: "ss_checkout_url",
  consentState: "ss_consent",
};

export const storage = {
  saveQuiz: (answers: Record<string, any>) => {
    try { localStorage.setItem(KEYS.quiz, JSON.stringify(answers)); } catch {}
  },
  getQuiz: (): Record<string, any> => {
    try { return JSON.parse(localStorage.getItem(KEYS.quiz) ?? "{}"); } catch { return {}; }
  },
  saveAnalysisId: (id: string) => {
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
  saveConsentState: (state: Record<string, boolean>) => {
    try { localStorage.setItem(KEYS.consentState, JSON.stringify(state)); } catch {}
  },
  getConsentState: (): Record<string, boolean> => {
    try { return JSON.parse(localStorage.getItem(KEYS.consentState) ?? "{}"); } catch { return {}; }
  },
};
