import React, { useEffect, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { storage } from "../services/storage";

const VALUE_PROPS = [
  "Análisis biométrico de la forma de tu rostro, proporciones craneales y asimetría.",
  "3 cortes a medida con instrucciones exactas: número de máquina, tipo de degradado, técnica.",
  "Guía de barba adaptada a la fortaleza de tu mandíbula y rasgos faciales específicos.",
];

export default function HomeScreen() {
  const navigation = useNavigation<any>();
  const [barberCode, setBarberCode] = useState("");
  const [codeApplied, setCodeApplied] = useState(false);
  const [resumeId, setResumeId] = useState<string | null>(null);

  useEffect(() => {
    storage.loadAnalysisId().then((id) => { if (id) setResumeId(id); });
    storage.loadBarberCode().then((code) => { if (code) { setBarberCode(code); setCodeApplied(true); } });
  }, []);

  const applyCode = async () => {
    const clean = barberCode.trim().toUpperCase();
    if (!clean) return;
    await storage.saveBarberCode(clean);
    setBarberCode(clean);
    setCodeApplied(true);
  };

  const handleStart = () => {
    navigation.navigate("Quiz", { barberCode: codeApplied ? barberCode : undefined });
  };

  const price = codeApplied ? "4,99" : "5,99";

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Wordmark */}
        <Text style={styles.wordmark}>STYLESCAN</Text>

        {/* Hero */}
        <View style={styles.hero}>
          <Text style={styles.headline}>El corte{"\n"}que realmente{"\n"}te favorece.</Text>
          <Text style={styles.tagline}>
            Análisis facial por IA. 468 puntos de medición.{"\n"}No tendencias — geometría.
          </Text>
        </View>

        {/* Divider */}
        <View style={styles.hairline} />

        {/* Value props — numbered editorial */}
        <View style={styles.props}>
          {VALUE_PROPS.map((text, i) => (
            <View key={i} style={styles.propRow}>
              <Text style={styles.propNum}>0{i + 1}</Text>
              <Text style={styles.propText}>{text}</Text>
            </View>
          ))}
        </View>

        {/* Resume banner */}
        {resumeId && (
          <TouchableOpacity
            style={styles.resumeBanner}
            onPress={() => navigation.navigate("Result", { analysisId: resumeId })}
          >
            <Text style={styles.resumeLabel}>ANÁLISIS EN CURSO</Text>
            <Text style={styles.resumeLink}>Continuar donde lo dejaste →</Text>
          </TouchableOpacity>
        )}

        {/* Barber code */}
        <View style={styles.codeBlock}>
          <Text style={styles.codeLabel}>CÓDIGO DE BARBERO  ·  OPCIONAL</Text>
          <View style={styles.codeRow}>
            <TextInput
              style={[styles.codeInput, codeApplied && styles.codeInputDone]}
              placeholder="STYLESCAN-XXXX"
              placeholderTextColor={COLORS.textMuted}
              value={barberCode}
              onChangeText={(t) => { setBarberCode(t); setCodeApplied(false); }}
              autoCapitalize="characters"
              autoCorrect={false}
            />
            <TouchableOpacity
              style={[styles.applyBtn, codeApplied && styles.applyBtnDone]}
              onPress={applyCode}
              disabled={codeApplied || !barberCode.trim()}
            >
              <Text style={[styles.applyBtnText, codeApplied && styles.applyBtnTextDone]}>
                {codeApplied ? "Aplicado" : "Usar"}
              </Text>
            </TouchableOpacity>
          </View>
          {codeApplied && (
            <Text style={styles.codeSuccess}>Descuento aplicado — pagarás 4,99 € en vez de 5,99 €</Text>
          )}
        </View>

        {/* Price + CTA */}
        <View style={styles.ctaBlock}>
          <View style={styles.priceRow}>
            <Text style={styles.price}>{price} €</Text>
            {codeApplied && <Text style={styles.priceStrike}>5,99 €</Text>}
            <Text style={styles.priceSub}>· pago único</Text>
          </View>

          <TouchableOpacity style={styles.startBtn} onPress={handleStart} activeOpacity={0.85}>
            <Text style={styles.startBtnText}>Comenzar análisis</Text>
            <View style={styles.startArrow}>
              <Text style={styles.startArrowText}>→</Text>
            </View>
          </TouchableOpacity>

          <Text style={styles.disclaimer}>
            Las fotos se borran al instante tras el análisis. Solo se guardan métricas numéricas, 90 días.
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  scroll: {
    paddingHorizontal: SPACING.lg,
    paddingTop: Platform.OS === "ios" ? 72 : 52,
    paddingBottom: 60,
  },

  wordmark: {
    color: COLORS.accent,
    fontSize: 10,
    letterSpacing: 5,
    fontWeight: "600" as const,
    marginBottom: SPACING.xl,
  },

  hero: { marginBottom: SPACING.lg },
  headline: {
    color: COLORS.text,
    fontSize: 44,
    lineHeight: 48,
    fontWeight: "700" as const,
    letterSpacing: -2,
    marginBottom: SPACING.md,
  },
  tagline: {
    color: COLORS.textMuted,
    fontSize: 14,
    lineHeight: 21,
  },

  hairline: {
    height: 1,
    backgroundColor: COLORS.border,
    marginBottom: SPACING.lg,
  },

  props: { gap: SPACING.lg, marginBottom: SPACING.xl },
  propRow: { flexDirection: "row", gap: SPACING.md, alignItems: "flex-start" },
  propNum: {
    color: COLORS.accent,
    fontSize: 10,
    fontWeight: "700" as const,
    letterSpacing: 1,
    paddingTop: 3,
    width: 24,
  },
  propText: { color: COLORS.textMuted, fontSize: 14, lineHeight: 20, flex: 1 },

  resumeBanner: {
    borderLeftWidth: 2,
    borderLeftColor: COLORS.accent,
    paddingLeft: SPACING.md,
    paddingVertical: SPACING.sm,
    marginBottom: SPACING.xl,
  },
  resumeLabel: {
    color: COLORS.accent,
    fontSize: 9,
    letterSpacing: 2.5,
    fontWeight: "700" as const,
    marginBottom: 4,
  },
  resumeLink: { color: COLORS.text, fontSize: 14, ...FONTS.label },

  codeBlock: { marginBottom: SPACING.xl, gap: SPACING.sm },
  codeLabel: {
    color: COLORS.textMuted,
    fontSize: 9,
    letterSpacing: 2,
    fontWeight: "600" as const,
  },
  codeRow: { flexDirection: "row", gap: SPACING.sm },
  codeInput: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
    color: COLORS.text,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm + 2,
    fontSize: 14,
    fontFamily: "monospace",
    letterSpacing: 1,
  },
  codeInputDone: { borderColor: COLORS.success },
  applyBtn: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: SPACING.md,
    justifyContent: "center",
  },
  applyBtnDone: { borderColor: COLORS.success },
  applyBtnText: { color: COLORS.textMuted, fontSize: 13, ...FONTS.label },
  applyBtnTextDone: { color: COLORS.success },
  codeSuccess: { color: COLORS.success, fontSize: 12 },

  ctaBlock: { gap: SPACING.md },
  priceRow: { flexDirection: "row", alignItems: "baseline", gap: 8 },
  price: {
    color: COLORS.text,
    fontSize: 48,
    fontWeight: "700" as const,
    letterSpacing: -2.5,
  },
  priceStrike: {
    color: COLORS.textMuted,
    fontSize: 20,
    textDecorationLine: "line-through",
    fontWeight: "400" as const,
  },
  priceSub: { color: COLORS.textMuted, fontSize: 13, alignSelf: "flex-end", paddingBottom: 8 },

  startBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.md + 4,
    paddingLeft: SPACING.lg,
    paddingRight: SPACING.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  startBtnText: {
    color: COLORS.primary,
    fontSize: 17,
    fontWeight: "700" as const,
    letterSpacing: -0.4,
  },
  startArrow: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(0,0,0,0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  startArrowText: { color: COLORS.primary, fontSize: 18, fontWeight: "700" as const },

  disclaimer: {
    color: COLORS.textMuted,
    fontSize: 11,
    lineHeight: 16,
    marginTop: SPACING.sm,
  },
});
