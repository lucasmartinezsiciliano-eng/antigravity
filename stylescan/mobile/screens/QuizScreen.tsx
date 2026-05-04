/**
 * QuizScreen — Pre-analysis preferences quiz
 * 6 questions, one per screen, swipeable forward/back.
 * Answers are passed to the backend to personalize the Claude report.
 */

import React, { useState } from "react";
import {
  Animated,
  Dimensions,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  TextInput,
  Platform,
} from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { QuizAnswers } from "../services/api";
import { storage } from "../services/storage";

const { width: W } = Dimensions.get("window");

// ─── Quiz step definitions ────────────────────────────────────────────────────

interface Option {
  value: string;
  label: string;
  sublabel?: string;
  emoji: string;
}

interface QuizStep {
  key: keyof QuizAnswers;
  question: string;
  subtitle?: string;
  type: "single" | "multi" | "text";
  options?: Option[];
  placeholder?: string;
}

const STEPS: QuizStep[] = [
  {
    key: "hair_texture",
    question: "¿Cómo es tu cabello naturalmente?",
    subtitle: "Sin productos. Recién lavado y seco.",
    type: "single",
    options: [
      { value: "straight", label: "Liso", sublabel: "Cae recto sin forma", emoji: "➖" },
      { value: "wavy",     label: "Ondulado", sublabel: "Forma olas suaves", emoji: "〰️" },
      { value: "curly",    label: "Rizado", sublabel: "Rizos definidos", emoji: "🌀" },
      { value: "coily",    label: "Muy rizado", sublabel: "Afro o coily", emoji: "⬛" },
    ],
  },
  {
    key: "hair_density",
    question: "¿Cuánto pelo tienes?",
    subtitle: "Agarra un mechón. ¿Cuánto ves entre los dedos?",
    type: "single",
    options: [
      { value: "thin",   label: "Fino / escaso", sublabel: "Se ven mucho el cuero cabelludo", emoji: "🔹" },
      { value: "medium", label: "Normal", sublabel: "Ni mucho ni poco", emoji: "🔷" },
      { value: "thick",  label: "Grueso / abundante", sublabel: "Pelo denso, pesa", emoji: "💎" },
    ],
  },
  {
    key: "preferred_length",
    question: "¿Qué longitud te gusta?",
    subtitle: "Tu preferencia ideal, no la que tienes ahora.",
    type: "single",
    options: [
      { value: "very_short", label: "Muy corto", sublabel: "Rapado o casi rapado", emoji: "⚡" },
      { value: "short",      label: "Corto", sublabel: "1 a 3 cm en el tope", emoji: "✂️" },
      { value: "medium",     label: "Medio", sublabel: "3 a 6 cm, peinables", emoji: "🌊" },
      { value: "long",       label: "Largo", sublabel: "Más de 6 cm", emoji: "🎸" },
    ],
  },
  {
    key: "maintenance_willingness",
    question: "¿Cuánto tiempo le dedicas al pelo?",
    subtitle: "Honestidad total. Esto afecta mucho a la recomendación.",
    type: "single",
    options: [
      { value: "low",    label: "Mínimo", sublabel: "Ducha y listo, sin producto", emoji: "😴" },
      { value: "medium", label: "Algo", sublabel: "2-3 minutos con producto", emoji: "⏱️" },
      { value: "high",   label: "Lo que haga falta", sublabel: "Me gusta cuidar mi imagen", emoji: "💪" },
    ],
  },
  {
    key: "style_preference",
    question: "¿Cómo describes tu estilo?",
    type: "single",
    options: [
      { value: "classic", label: "Clásico", sublabel: "Conservador, formal", emoji: "🎩" },
      { value: "modern",  label: "Moderno", sublabel: "Urbano, limpio", emoji: "🏙️" },
      { value: "trendy",  label: "A la moda", sublabel: "Arriesgado, llamativo", emoji: "🔥" },
    ],
  },
  {
    key: "beard",
    question: "¿Llevas barba?",
    type: "single",
    options: [
      { value: "none",    label: "Sin barba", sublabel: "Afeitado", emoji: "🧼" },
      { value: "stubble", label: "Barba de días", sublabel: "1-3 días", emoji: "🪒" },
      { value: "short",   label: "Barba corta", sublabel: "Menos de 2 cm", emoji: "🧔" },
      { value: "full",    label: "Barba completa", sublabel: "Más de 2 cm", emoji: "🧔‍♂️" },
    ],
  },
  {
    key: "problematic_areas",
    question: "¿Alguna zona problemática?",
    subtitle: "Selecciona todas las que apliquen (opcional).",
    type: "multi",
    options: [
      { value: "entradas",     label: "Entradas", sublabel: "Línea de nacimiento retrocediendo", emoji: "↩️" },
      { value: "coronilla",    label: "Coronilla escasa", sublabel: "Pelándose en el centro", emoji: "⭕" },
      { value: "remolino",     label: "Remolino fuerte", sublabel: "El pelo no cae bien", emoji: "🌀" },
      { value: "pelo_fino",    label: "Pelo muy fino", sublabel: "Sin volumen", emoji: "💨" },
      { value: "asimetria",    label: "Asimetría", sublabel: "Un lado diferente al otro", emoji: "⚖️" },
      { value: "ninguna",      label: "Ninguna", sublabel: "", emoji: "✅" },
    ],
  },
  {
    key: "additional_notes",
    question: "¿Algo más que quieras que tengamos en cuenta?",
    subtitle: "Opcional. Cuéntanos lo que quieras.",
    type: "text",
    placeholder: "Ej: Quiero algo que no requiera secador, o que favorezca con gafas...",
  },
];

// ─── Component ────────────────────────────────────────────────────────────────

export default function QuizScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { barberCode } = route.params ?? {};

  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Partial<QuizAnswers>>({});
  const slideAnim = React.useRef(new Animated.Value(0)).current;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;
  const canAdvance =
    current.type === "text" ||
    (current.type === "single" && answers[current.key] !== undefined) ||
    (current.type === "multi" && (answers[current.key] as string[] | undefined)?.length);

  const animateNext = (dir: 1 | -1) => {
    Animated.sequence([
      Animated.timing(slideAnim, { toValue: -30 * dir, duration: 120, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 180, useNativeDriver: true }),
    ]).start();
  };

  const handleSelect = (value: string) => {
    if (current.type === "single") {
      setAnswers((a) => ({ ...a, [current.key]: value }));
    } else if (current.type === "multi") {
      const prev = (answers[current.key] as string[]) ?? [];
      if (value === "ninguna") {
        setAnswers((a) => ({ ...a, [current.key]: ["ninguna"] }));
      } else {
        const filtered = prev.filter((v) => v !== "ninguna");
        const next = filtered.includes(value)
          ? filtered.filter((v) => v !== value)
          : [...filtered, value];
        setAnswers((a) => ({ ...a, [current.key]: next }));
      }
    }
  };

  const handleNext = async () => {
    if (!canAdvance) return;
    if (isLast) {
      await storage.saveQuiz(answers);
      navigation.navigate("Consent", {
        quizAnswers: answers,
        barberCode,
      });
      return;
    }
    animateNext(1);
    setStep((s) => s + 1);
  };

  const handleBack = () => {
    if (step === 0) { navigation.goBack(); return; }
    animateNext(-1);
    setStep((s) => s - 1);
  };

  const isSelected = (value: string) => {
    const v = answers[current.key];
    if (current.type === "multi") return (v as string[] | undefined)?.includes(value) ?? false;
    return v === value;
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backBtn}>
          <Text style={styles.backTxt}>←</Text>
        </TouchableOpacity>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${((step + 1) / STEPS.length) * 100}%` }]} />
        </View>
        <Text style={styles.stepCount}>{step + 1}/{STEPS.length}</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Animated.View style={{ transform: [{ translateX: slideAnim }] }}>
          <Text style={styles.question}>{current.question}</Text>
          {current.subtitle && <Text style={styles.subtitle}>{current.subtitle}</Text>}

          {/* Single / multi options */}
          {current.options && (
            <View style={styles.options}>
              {current.options.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  style={[styles.option, isSelected(opt.value) && styles.optionSelected]}
                  onPress={() => handleSelect(opt.value)}
                  activeOpacity={0.75}
                >
                  <Text style={styles.optionEmoji}>{opt.emoji}</Text>
                  <View style={styles.optionText}>
                    <Text style={[styles.optionLabel, isSelected(opt.value) && styles.optionLabelSelected]}>
                      {opt.label}
                    </Text>
                    {opt.sublabel ? (
                      <Text style={styles.optionSub}>{opt.sublabel}</Text>
                    ) : null}
                  </View>
                  {isSelected(opt.value) && <Text style={styles.check}>✓</Text>}
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Free text */}
          {current.type === "text" && (
            <TextInput
              style={styles.textInput}
              multiline
              numberOfLines={4}
              placeholder={current.placeholder}
              placeholderTextColor={COLORS.textMuted}
              value={(answers[current.key] as string) ?? ""}
              onChangeText={(t) => setAnswers((a) => ({ ...a, [current.key]: t }))}
            />
          )}
        </Animated.View>
      </ScrollView>

      {/* Next button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.nextBtn, !canAdvance && styles.nextBtnDisabled]}
          onPress={handleNext}
          disabled={!canAdvance}
        >
          <Text style={styles.nextBtnText}>
            {isLast ? "Ver mis resultados →" : "Siguiente →"}
          </Text>
        </TouchableOpacity>
        {current.type !== "single" && (
          <TouchableOpacity onPress={handleNext} style={styles.skipLink}>
            <Text style={styles.skipLinkText}>Saltar esta pregunta</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingTop: Platform.OS === "ios" ? 56 : 36,
    paddingHorizontal: SPACING.md,
    paddingBottom: SPACING.md,
    gap: SPACING.sm,
  },
  backBtn: { padding: SPACING.sm },
  backTxt: { color: COLORS.text, fontSize: 22 },
  progressBar: {
    flex: 1,
    height: 3,
    backgroundColor: COLORS.border,
    borderRadius: 2,
    overflow: "hidden",
  },
  progressFill: { height: "100%", backgroundColor: COLORS.accent, borderRadius: 2 },
  stepCount: { color: COLORS.textMuted, fontSize: 12, ...FONTS.label, width: 32, textAlign: "right" },

  scroll: { padding: SPACING.lg, paddingBottom: 160 },
  question: { color: COLORS.text, fontSize: 24, ...FONTS.heading, marginBottom: SPACING.sm },
  subtitle: { color: COLORS.textMuted, fontSize: 14, lineHeight: 20, marginBottom: SPACING.lg },

  options: { gap: SPACING.sm },
  option: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    padding: SPACING.md,
    gap: SPACING.md,
  },
  optionSelected: { borderColor: COLORS.accent, backgroundColor: "rgba(201,168,76,0.08)" },
  optionEmoji: { fontSize: 24, width: 32, textAlign: "center" },
  optionText: { flex: 1 },
  optionLabel: { color: COLORS.text, fontSize: 16, ...FONTS.label },
  optionLabelSelected: { color: COLORS.accent },
  optionSub: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },
  check: { color: COLORS.accent, fontSize: 18, fontWeight: "700" },

  textInput: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    color: COLORS.text,
    padding: SPACING.md,
    fontSize: 15,
    lineHeight: 22,
    minHeight: 120,
    textAlignVertical: "top",
  },

  footer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: SPACING.lg,
    paddingBottom: Platform.OS === "ios" ? 40 : SPACING.lg,
    backgroundColor: COLORS.bg,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.sm,
  },
  nextBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.pill,
    paddingVertical: SPACING.md,
    alignItems: "center",
  },
  nextBtnDisabled: { opacity: 0.35 },
  nextBtnText: { color: COLORS.primary, fontSize: 17, ...FONTS.heading },
  skipLink: { alignItems: "center", paddingVertical: SPACING.sm },
  skipLinkText: { color: COLORS.textMuted, fontSize: 13 },
});
