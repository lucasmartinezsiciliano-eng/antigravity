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

interface Option { value: string; label: string; sublabel?: string; emoji: string; }
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
    subtitle: "Sin productos. Recién lavado y seco al aire.",
    type: "single",
    options: [
      { value: "straight", label: "Liso",        sublabel: "Cae recto sin forma",      emoji: "➖" },
      { value: "wavy",     label: "Ondulado",     sublabel: "Forma olas suaves",        emoji: "〰️" },
      { value: "curly",    label: "Rizado",       sublabel: "Rizos definidos",          emoji: "🌀" },
      { value: "coily",   label: "Muy rizado",   sublabel: "Afro o muy apretado",      emoji: "⬛" },
    ],
  },
  {
    key: "hair_density",
    question: "¿Cuánto pelo tienes?",
    subtitle: "Agarra un mechón. ¿Cuánto cuero cabelludo ves entre los dedos?",
    type: "single",
    options: [
      { value: "thin",   label: "Fino / escaso",        sublabel: "Se ve mucho el cuero",    emoji: "🔹" },
      { value: "medium", label: "Normal",                sublabel: "Ni mucho ni poco",        emoji: "🔷" },
      { value: "thick",  label: "Grueso / abundante",   sublabel: "Denso, pesa bastante",    emoji: "💎" },
    ],
  },
  {
    key: "lifestyle",
    question: "¿Cuál es tu entorno habitual?",
    subtitle: "Esto define qué estilos son viables para tu día a día.",
    type: "single",
    options: [
      { value: "professional", label: "Oficina / profesional", sublabel: "Reuniones, clientes, formal",   emoji: "🏢" },
      { value: "creative",     label: "Sector creativo",       sublabel: "Agencia, arte, casual",         emoji: "🎨" },
      { value: "active",       label: "Físico / deportivo",    sublabel: "Obra, deporte, aire libre",     emoji: "⚡" },
      { value: "mixed",        label: "Mixto / desde casa",    sublabel: "Variado, sin código fijo",      emoji: "🏠" },
    ],
  },
  {
    key: "style_goal",
    question: "¿Qué quieres conseguir con tu corte?",
    subtitle: "Sé honesto. Esto guía toda la recomendación.",
    type: "single",
    options: [
      { value: "professional_look", label: "Verme más profesional", sublabel: "Cuidado, serio, imagen sólida",    emoji: "💼" },
      { value: "trendy_look",       label: "Seguir las tendencias", sublabel: "Actual, llamativo, con personalidad", emoji: "📱" },
      { value: "effortless_look",   label: "Bien sin esfuerzo",     sublabel: "Natural, sin complicaciones",        emoji: "😎" },
      { value: "confidence_boost",  label: "Ganar confianza",       sublabel: "Un cambio real, reinventarme",       emoji: "🔥" },
    ],
  },
  {
    key: "preferred_length",
    question: "¿Qué longitud te gusta?",
    subtitle: "Tu preferencia ideal, no la que tienes ahora.",
    type: "single",
    options: [
      { value: "very_short", label: "Muy corto",  sublabel: "Rapado o casi",             emoji: "⚡" },
      { value: "short",      label: "Corto",      sublabel: "1-3 cm en el tope",         emoji: "✂️" },
      { value: "medium",     label: "Medio",      sublabel: "3-6 cm, peinables",         emoji: "🌊" },
      { value: "long",       label: "Largo",      sublabel: "Más de 6 cm",               emoji: "🎸" },
    ],
  },
  {
    key: "maintenance_willingness",
    question: "¿Cuánto tiempo le dedicas al pelo por las mañanas?",
    subtitle: "Con total honestidad. Afecta mucho a qué corte funciona contigo.",
    type: "single",
    options: [
      { value: "low",    label: "Menos de 2 min",   sublabel: "Ducha y listo, sin producto",         emoji: "😴" },
      { value: "medium", label: "Unos 5 min",        sublabel: "Un poco de producto, nada más",      emoji: "⏱️" },
      { value: "high",   label: "10 min o más",      sublabel: "Secador, producto, lo que toque",   emoji: "💪" },
    ],
  },
  {
    key: "beard",
    question: "¿Llevas barba habitualmente?",
    subtitle: "El corte y la barba se diseñan juntos.",
    type: "single",
    options: [
      { value: "none",     label: "Sin barba",       sublabel: "Siempre afeitado",             emoji: "" },
      { value: "stubble",  label: "Barba de días",   sublabel: "3-10 días, perfilada",         emoji: "" },
      { value: "goatee",   label: "Perilla",          sublabel: "Solo en mentón, sin mejillas", emoji: "" },
      { value: "mustache", label: "Solo bigote",      sublabel: "Sobre el labio, sin barba",    emoji: "" },
      { value: "short",    label: "Barba corta",      sublabel: "Menos de 2 cm",                emoji: "" },
      { value: "full",     label: "Barba completa",   sublabel: "Más de 2 cm, llena",           emoji: "" },
    ],
  },
  {
    key: "problematic_areas",
    question: "¿Hay alguna zona que te preocupe?",
    subtitle: "Selecciona todas las que apliquen. Es opcional pero muy útil.",
    type: "multi",
    options: [
      { value: "entradas",     label: "Entradas",           sublabel: "Línea retrocediendo",          emoji: "↩️" },
      { value: "coronilla",    label: "Coronilla escasa",   sublabel: "Pelándose en el centro",       emoji: "⭕" },
      { value: "remolino",     label: "Remolino fuerte",    sublabel: "El pelo no cae bien",          emoji: "🌀" },
      { value: "pelo_fino",    label: "Pelo muy fino",      sublabel: "Sin volumen",                  emoji: "💨" },
      { value: "asimetria",    label: "Asimetría",          sublabel: "Un lado diferente al otro",    emoji: "⚖️" },
      { value: "ninguna",      label: "Ninguna",            sublabel: "",                             emoji: "✅" },
    ],
  },
  {
    key: "reference_style",
    question: "¿Hay algún corte o estilo que te haya gustado antes?",
    subtitle: "Opcional. Un nombre, una descripción, o nada. Ayuda a afinar la recomendación.",
    type: "text",
    placeholder: "Ej: Me gustó el degradado que llevaba hace 2 años, o el estilo de Brad Pitt en Fury...",
  },
  {
    key: "additional_notes",
    question: "¿Algo más que tengamos en cuenta?",
    subtitle: "Opcional. Lo que quieras que sepa el análisis.",
    type: "text",
    placeholder: "Ej: Uso gafas, trabajo en un entorno muy conservador, quiero algo que no requiera secador...",
  },
];

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
      Animated.timing(slideAnim, { toValue: 0,         duration: 180, useNativeDriver: true }),
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
      navigation.navigate("Consent", { quizAnswers: answers, barberCode });
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

          {current.options && (
            <View style={styles.options}>
              {current.options.map((opt) => (
                <TouchableOpacity
                  key={opt.value}
                  style={[styles.option, isSelected(opt.value) && styles.optionSelected]}
                  onPress={() => handleSelect(opt.value)}
                  activeOpacity={0.75}
                >
                  <View style={styles.optionText}>
                    <Text style={[styles.optionLabel, isSelected(opt.value) && styles.optionLabelSelected]}>
                      {opt.label}
                    </Text>
                    {opt.sublabel ? <Text style={styles.optionSub}>{opt.sublabel}</Text> : null}
                  </View>
                  {isSelected(opt.value)
                    ? <Text style={styles.check}>✓</Text>
                    : <View style={styles.uncheck} />}
                </TouchableOpacity>
              ))}
            </View>
          )}

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

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.nextBtn, !canAdvance && styles.nextBtnDisabled]}
          onPress={handleNext}
          disabled={!canAdvance}
          activeOpacity={0.85}
        >
          <Text style={styles.nextBtnText}>
            {isLast ? "Ver mis resultados" : "Siguiente"}
          </Text>
          <View style={styles.nextBtnArrow}>
            <Text style={styles.nextBtnArrowText}>→</Text>
          </View>
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
  backTxt: { color: COLORS.text, fontSize: 20, fontWeight: "300" as const },
  progressBar: { flex: 1, height: 2, backgroundColor: COLORS.border, borderRadius: 1, overflow: "hidden" },
  progressFill: { height: "100%", backgroundColor: COLORS.accent },
  stepCount: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontWeight: "600" as const,
    letterSpacing: 0.5,
    width: 32,
    textAlign: "right" as const,
  },

  scroll: { paddingHorizontal: SPACING.lg, paddingTop: SPACING.md, paddingBottom: 160 },
  question: {
    color: COLORS.text,
    fontSize: 26,
    fontWeight: "700" as const,
    letterSpacing: -0.8,
    marginBottom: SPACING.sm,
    lineHeight: 32,
  },
  subtitle: { color: COLORS.textMuted, fontSize: 13, lineHeight: 19, marginBottom: SPACING.lg },

  options: { gap: 0 },
  option: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.md,
    gap: SPACING.md,
    borderLeftWidth: 2,
    borderLeftColor: "transparent",
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  optionSelected: { borderLeftColor: COLORS.accent, backgroundColor: "rgba(201,168,76,0.05)" },
  optionText: { flex: 1 },
  optionLabel: { color: COLORS.text, fontSize: 15, ...FONTS.label },
  optionLabelSelected: { color: COLORS.accent },
  optionSub: { color: COLORS.textMuted, fontSize: 12, marginTop: 2, fontWeight: "400" as const },
  check: {
    color: COLORS.accent,
    fontSize: 14,
    fontWeight: "700" as const,
    width: 22,
    textAlign: "center" as const,
  },
  uncheck: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },

  textInput: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderLeftWidth: 2,
    borderLeftColor: COLORS.accent,
    color: COLORS.text,
    padding: SPACING.md,
    fontSize: 15,
    lineHeight: 22,
    minHeight: 120,
    textAlignVertical: "top" as const,
  },

  footer: {
    position: "absolute", bottom: 0, left: 0, right: 0,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.md,
    paddingBottom: Platform.OS === "ios" ? 40 : SPACING.lg,
    backgroundColor: COLORS.bg,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.sm,
  },
  nextBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.md + 2,
    paddingLeft: SPACING.lg,
    paddingRight: SPACING.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  nextBtnDisabled: { opacity: 0.3 },
  nextBtnText: { color: COLORS.primary, fontSize: 16, fontWeight: "700" as const, letterSpacing: -0.3 },
  nextBtnArrow: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: "rgba(0,0,0,0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  nextBtnArrowText: { color: COLORS.primary, fontSize: 16, fontWeight: "700" as const },
  skipLink: { alignItems: "center", paddingVertical: SPACING.sm },
  skipLinkText: { color: COLORS.textMuted, fontSize: 12, letterSpacing: 0.3 },
});
