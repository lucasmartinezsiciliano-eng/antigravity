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
  saveQuiz: (q: Partial<QuizAnswers>) =>
    AsyncStorage.setItem(KEYS.QUIZ, JSON.stringify(q)),

  loadQuiz: async (): Promise<Partial<QuizAnswers> | null> => {
    const raw = await AsyncStorage.getItem(KEYS.QUIZ);
    return raw ? JSON.parse(raw) : null;
  },

  saveAnalysisId: (id: string) =>
    AsyncStorage.setItem(KEYS.ANALYSIS_ID, id),

  loadAnalysisId: () => AsyncStorage.getItem(KEYS.ANALYSIS_ID),

  saveBarberCode: (code: string) =>
    AsyncStorage.setItem(KEYS.BARBER_CODE, code),

  loadBarberCode: () => AsyncStorage.getItem(KEYS.BARBER_CODE),

  clear: () => AsyncStorage.multiRemove(Object.values(KEYS)),
};
