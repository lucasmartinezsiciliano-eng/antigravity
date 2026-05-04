/**
 * PaymentPendingScreen — Shown after redirecting to Stripe.
 * Instructs user to complete payment in browser. Once confirmed,
 * they proceed to capture.
 *
 * The backend confirms payment via webhook. We poll until status = "paid".
 */

import React, { useEffect, useRef } from "react";
import { Animated, Easing, Platform, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { api } from "../services/api";

export default function PaymentPendingScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { analysis_id } = route.params;

  const pulseAnim = useRef(new Animated.Value(1)).current;
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Pulse animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.12, duration: 700, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 700, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();

    // Poll every 4 seconds for payment confirmation
    intervalRef.current = setInterval(async () => {
      try {
        const result = await api.getResult(analysis_id);
        // If we get a result back (not 402), payment went through
        if (result.analysis_id) {
          clearInterval(intervalRef.current!);
          navigation.replace("Capture", { analysisId: analysis_id });
        }
      } catch (e: any) {
        if (e.message?.includes("402")) return; // Still pending, keep polling
        if (e.message?.includes("202")) {
          // Paid and processing / completed already
          clearInterval(intervalRef.current!);
          navigation.replace("Result", { analysisId: analysis_id });
        }
      }
    }, 4000);

    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [analysis_id, navigation, pulseAnim]);

  const handleAlreadyPaid = () => {
    navigation.replace("Capture", { analysisId: analysis_id });
  };

  return (
    <View style={styles.container}>
      <Animated.Text style={[styles.icon, { transform: [{ scale: pulseAnim }] }]}>
        💳
      </Animated.Text>
      <Text style={styles.title}>Esperando confirmación del pago</Text>
      <Text style={styles.subtitle}>
        Completa el pago en el navegador que se acaba de abrir.{"\n"}
        Volveremos aquí automáticamente cuando confirme.
      </Text>

      <View style={styles.steps}>
        {[
          "Paga en el navegador",
          "Vuelve a StyleScan",
          "Haz las fotos",
          "Recibe tu informe",
        ].map((step, i) => (
          <View key={i} style={styles.stepRow}>
            <View style={[styles.stepDot, i === 1 && styles.stepDotActive]}>
              <Text style={styles.stepDotText}>{i + 1}</Text>
            </View>
            <Text style={[styles.stepText, i === 1 && styles.stepTextActive]}>{step}</Text>
          </View>
        ))}
      </View>

      <TouchableOpacity style={styles.alreadyBtn} onPress={handleAlreadyPaid}>
        <Text style={styles.alreadyBtnText}>Ya he pagado → Continuar</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.helpLink} onPress={() => navigation.goBack()}>
        <Text style={styles.helpLinkText}>← Volver al inicio</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1, backgroundColor: COLORS.bg,
    alignItems: "center", justifyContent: "center",
    padding: SPACING.xl,
  },
  icon: { fontSize: 72, marginBottom: SPACING.lg },
  title: { color: COLORS.text, fontSize: 22, ...FONTS.heading, textAlign: "center", marginBottom: SPACING.sm },
  subtitle: { color: COLORS.textMuted, fontSize: 15, lineHeight: 22, textAlign: "center", marginBottom: SPACING.xl },

  steps: { gap: SPACING.md, width: "100%", marginBottom: SPACING.xl },
  stepRow: { flexDirection: "row", alignItems: "center", gap: SPACING.md },
  stepDot: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: COLORS.surface, borderWidth: 1.5, borderColor: COLORS.border,
    alignItems: "center", justifyContent: "center",
  },
  stepDotActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  stepDotText: { color: COLORS.text, fontSize: 13, ...FONTS.label },
  stepText: { color: COLORS.textMuted, fontSize: 15 },
  stepTextActive: { color: COLORS.text, ...FONTS.label },

  alreadyBtn: {
    backgroundColor: COLORS.accent, borderRadius: RADIUS.pill,
    paddingVertical: SPACING.md, paddingHorizontal: SPACING.xl,
    marginBottom: SPACING.md,
  },
  alreadyBtnText: { color: COLORS.primary, fontSize: 16, ...FONTS.heading },
  helpLink: { padding: SPACING.sm },
  helpLinkText: { color: COLORS.textMuted, fontSize: 14 },
});
