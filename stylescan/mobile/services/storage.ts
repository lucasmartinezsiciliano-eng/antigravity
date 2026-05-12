/**
 * Local state persistence — quiz answers, active analysis ID, etc.
 * Uses AsyncStorage (expo-sqlite alternative for simple key-value).
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { QuizAnswers } from "./api";

const KEYS = {
  QUIZ: "stylescan:quiz",
  ANALYSIS_ID: "stylescan:analysis_id",
  BARBER_CODE: "stylescan:barber_code",
} as const;

export const storage = {
  saveQuiz: async (q: Partial<QuizAnswers>): Promise<void> => {
    try {
      await AsyncStorage.setItem(KEYS.QUIZ, JSON.stringify(q));
    } catch { /* non-critical — quiz will be re-entered if lost */ }
  },

  loadQuiz: async (): Promise<Partial<QuizAnswers> | null> => {
    try {
      const raw = await AsyncStorage.getItem(KEYS.QUIZ);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  saveAnalysisId: async (id: string): Promise<void> => {
    try {
      await AsyncStorage.setItem(KEYS.ANALYSIS_ID, id);
    } catch { /* non-critical */ }
  },

  loadAnalysisId: async (): Promise<string | null> => {
    try {
      return await AsyncStorage.getItem(KEYS.ANALYSIS_ID);
    } catch {
      return null;
    }
  },

  saveBarberCode: async (code: string): Promise<void> => {
    try {
      await AsyncStorage.setItem(KEYS.BARBER_CODE, code);
    } catch { /* non-critical */ }
  },

  loadBarberCode: async (): Promise<string | null> => {
    try {
      return await AsyncStorage.getItem(KEYS.BARBER_CODE);
    } catch {
      return null;
    }
  },

  clear: async (): Promise<void> => {
    try {
      await AsyncStorage.multiRemove(Object.values(KEYS));
    } catch { /* best-effort */ }
  },
};
