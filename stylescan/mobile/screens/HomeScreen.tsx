/**
 * HomeScreen — Landing page
 * Entry point: enter barber code (optional) → start quiz → consent → pay → capture → result
 */

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

export default function HomeScreen() {
  const navigation = useNavigation<any>();
  const [barberCode, setBarberCode] = useState("");
  const [codeApplied, setCodeApplied] = useState(false);
  const [resumeId, setResumeId] = useState<string | null>(null);

  useEffect(() => {
    // Check if there's an in-progress analysis to resume
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

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logo / hero */}
        <View style={styles.hero}>
          <Text style={styles.logo}>✦ StyleScan</Text>
          <Text style={styles.tagline}>
            Descubre exactamente qué corte de pelo te favorece. Basado en la forma de tu rostro, no en la moda.
          </Text>
        </View>

        {/* Value props */}
        <View style={styles.props}>
          {[
            { icon: "🔬", title: "Análisis facial por IA", sub: "468 puntos de medición en tu rostro" },
            { icon: "✂️", title: "3 cortes personalizados", sub: "Con instrucciones exactas para tu barbero" },
            { icon: "📄", title: "Informe descargable", sub: "Llévalo a cualquier barbería del mundo" },
          ].map((p) => (
            <View key={p.title} style={styles.propRow}>
              <Text style={styles.propIcon}>{p.icon}</Text>
              <View>
                <Text style={styles.propTitle}>{p.title}</Text>
                <Text style={styles.propSub}>{p.sub}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Barber code */}
        <View style={styles.codeBlock}>
          <Text style={styles.codeLabel}>
            ¿Tu barbero te dio un código? Ahorra 1 € y apóyale.
          </Text>
          <View style={styles.codeRow}>
            <TextInput
              style={styles.codeInput}
              placeholder="STYLESCAN-NOMBRE-XXXX"
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
              <Text style={styles.applyBtnText}>{codeApplied ? "✓" : "Aplicar"}</Text>
            </TouchableOpacity>
          </View>
          {codeApplied && (
            <Text style={styles.codeSuccess}>
              ✓ Código aplicado — pagarás 4,99 € en vez de 5,99 €
            </Text>
          )}
        </View>

        {/* Resume banner */}
        {resumeId && (
          <TouchableOpacity
            style={styles.resumeBanner}
            onPress={() => navigation.navigate("Result", { analysisId: resumeId })}
          >
            <Text style={styles.resumeText}>
              Tienes un análisis en curso. Ver resultado →
            </Text>
          </TouchableOpacity>
        )}

        {/* Price */}
        <View style={styles.priceBlock}>
          <View style={styles.priceRow}>
            <Text style={styles.price}>{codeApplied ? "4,99 €" : "5,99 €"}</Text>
            {codeApplied && <Text style={styles.priceOriginal}>5,99 €</Text>}
          </View>
          <Text style={styles.priceSub}>Pago único · Sin suscripción · Sin letra pequeña</Text>
        </View>

        {/* CTA */}
        <TouchableOpacity style={styles.startBtn} onPress={handleStart}>
          <Text style={styles.startBtnText}>Empezar análisis →</Text>
        </TouchableOpacity>

        <Text style={styles.disclaimer}>
          Tus fotos se borran inmediatamente tras el análisis. Solo guardamos las métricas numéricas durante 90 días.
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { padding: SPACING.lg, paddingTop: Platform.OS === "ios" ? 70 : 50, paddingBottom: 60 },

  hero: { marginBottom: SPACING.xl, alignItems: "center" },
  logo: { color: COLORS.accent, fontSize: 32, ...FONTS.heading, letterSpacing: 1, marginBottom: SPACING.md },
  tagline: { color: COLORS.textMuted, fontSize: 16, lineHeight: 24, textAlign: "center" },

  props: { gap: SPACING.md, marginBottom: SPACING.xl },
  propRow: { flexDirection: "row", gap: SPACING.md, alignItems: "flex-start", backgroundColor: COLORS.surface, borderRadius: RADIUS.md, padding: SPACING.md },
  propIcon: { fontSize: 28, width: 36, textAlign: "center" },
  propTitle: { color: COLORS.text, fontSize: 15, ...FONTS.label },
  propSub: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },

  codeBlock: { backgroundColor: COLORS.surface, borderRadius: RADIUS.md, padding: SPACING.md, marginBottom: SPACING.lg, gap: SPACING.sm },
  codeLabel: { color: COLORS.textMuted, fontSize: 13 },
  codeRow: { flexDirection: "row", gap: SPACING.sm },
  codeInput: {
    flex: 1, backgroundColor: COLORS.bg, borderRadius: RADIUS.sm,
    borderWidth: 1, borderColor: COLORS.border,
    color: COLORS.text, padding: SPACING.sm, fontSize: 14, ...FONTS.mono,
  },
  applyBtn: { backgroundColor: COLORS.border, borderRadius: RADIUS.sm, paddingHorizontal: SPACING.md, justifyContent: "center" },
  applyBtnDone: { backgroundColor: COLORS.success },
  applyBtnText: { color: COLORS.text, fontSize: 14, ...FONTS.label },
  codeSuccess: { color: COLORS.success, fontSize: 13 },

  resumeBanner: { backgroundColor: "rgba(201,168,76,0.12)", borderRadius: RADIUS.md, borderWidth: 1, borderColor: COLORS.accent, padding: SPACING.md, marginBottom: SPACING.md, alignItems: "center" },
  resumeText: { color: COLORS.accent, fontSize: 14, ...FONTS.label },

  priceBlock: { alignItems: "center", marginBottom: SPACING.lg, gap: 4 },
  priceRow: { flexDirection: "row", alignItems: "baseline", gap: SPACING.sm },
  price: { color: COLORS.text, fontSize: 40, ...FONTS.heading },
  priceOriginal: { color: COLORS.textMuted, fontSize: 20, textDecorationLine: "line-through" },
  priceSub: { color: COLORS.textMuted, fontSize: 13 },

  startBtn: { backgroundColor: COLORS.accent, borderRadius: RADIUS.pill, paddingVertical: SPACING.md + 4, alignItems: "center", marginBottom: SPACING.md },
  startBtnText: { color: COLORS.primary, fontSize: 18, ...FONTS.heading },

  disclaimer: { color: COLORS.textMuted, fontSize: 11, textAlign: "center", lineHeight: 16 },
});
