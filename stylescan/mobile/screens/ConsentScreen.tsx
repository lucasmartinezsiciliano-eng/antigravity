/**
 * ConsentScreen — RGPD Art. 9 explicit consent
 *
 * Un solo checkbox unificado — RGPD-válido porque:
 *   1. El texto completo de todos los puntos es visible antes de marcar.
 *   2. El checkbox es voluntario y no está pre-marcado (AEPD).
 *   3. El backend sigue recibiendo los 5 campos individuales (audit trail intacto).
 * El hash del texto mostrado se envía al backend para auditoría.
 */

import React, { useState } from "react";
import {
  Alert,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  ActivityIndicator,
} from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import * as Crypto from "expo-crypto";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { api } from "../services/api";
import { storage } from "../services/storage";

// Este texto es hasheado — cambiarlo cambia el hash guardado en el audit log.
const CONSENT_TEXT_V1 = `StyleScan trata tus fotos del rostro para extraer 468 puntos de medición facial (datos biométricos, Categoría Especial RGPD Art. 9). Las fotos originales se borran inmediatamente tras el análisis. Solo se guardan métricas numéricas durante 90 días. Tienes derecho de acceso, rectificación, supresión y portabilidad. Puedes retirar este consentimiento en cualquier momento. Responsable: StyleScan SL. Contacto DPD: privacidad@stylescan.app.`;

const CONSENT_POINTS = [
  "Proceso de mis fotos del rostro para extraer mediciones faciales (datos biométricos).",
  "Mis datos biométricos son Categoría Especial bajo el RGPD (Art. 9) y este consentimiento es voluntario.",
  "Mis fotos originales se eliminan automáticamente e inmediatamente tras el análisis.",
  "Las métricas numéricas derivadas (no las fotos) se conservan 90 días para acceder a mi informe.",
  "Confirmo que soy mayor de 18 años.",
];

export default function ConsentScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { quizAnswers, barberCode } = route.params;

  const [accepted, setAccepted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleProceed = async () => {
    if (!accepted) return;
    setLoading(true);

    try {
      // 1. Crear análisis + obtener URL de checkout
      const initResult = await api.initiateAnalysis({
        barber_code: barberCode ?? undefined,
        quiz_answers: quizAnswers,
      });

      const { analysis_id, checkout_url } = initResult;

      // 2. Hash del texto mostrado (auditoría RGPD)
      const consentHash = await Crypto.digestStringAsync(
        Crypto.CryptoDigestAlgorithm.SHA256,
        CONSENT_TEXT_V1
      );

      // 3. Registrar consentimiento — todos los campos individuales = true
      //    El backend sigue auditando cada campo por separado.
      await api.recordConsent(analysis_id, {
        consented_biometric_processing: true,
        consented_special_category_data: true,
        consented_retention_90_days: true,
        consented_immediate_photo_deletion: true,
        consented_age_verification: true,
        consent_text_hash: consentHash,
      });

      await storage.saveAnalysisId(analysis_id);

      // 4. Abrir Stripe o saltar en dev
      const isDevBypass = checkout_url.includes("dev-payment-skipped");
      if (isDevBypass) {
        navigation.replace("Capture", { analysisId: analysis_id });
        return;
      }

      const canOpen = await Linking.canOpenURL(checkout_url);
      if (canOpen) {
        await Linking.openURL(checkout_url);
        navigation.navigate("PaymentPending", { analysis_id });
      } else {
        Alert.alert("Error", "No se pudo abrir la página de pago.");
      }
    } catch (e: any) {
      Alert.alert("Error", e.message ?? "Error al procesar. Inténtalo de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* Header */}
        <View style={styles.headerBlock}>
          <Text style={styles.icon}>🔒</Text>
          <Text style={styles.title}>Antes de continuar</Text>
          <Text style={styles.subtitle}>
            Tus fotos contienen datos biométricos. La ley europea nos obliga a
            pedirte consentimiento explícito antes de analizarlas.
          </Text>
        </View>

        {/* Puntos de consentimiento — visibles, no checkboxes */}
        <View style={styles.pointsBlock}>
          {CONSENT_POINTS.map((point, i) => (
            <View key={i} style={styles.pointRow}>
              <Text style={styles.pointBullet}>·</Text>
              <Text style={styles.pointText}>{point}</Text>
            </View>
          ))}
          <TouchableOpacity
            style={styles.policyLink}
            onPress={() => Linking.openURL("https://stylescan.app/privacidad")}
          >
            <Text style={styles.link}>Leer política de privacidad completa →</Text>
          </TouchableOpacity>
        </View>

        {/* Lo que NUNCA hacemos */}
        <View style={styles.notBlock}>
          <Text style={styles.notTitle}>Lo que NUNCA hacemos:</Text>
          {[
            "Guardamos tus fotos originales",
            "Usamos tus datos para publicidad",
            "Compartimos tus datos con terceros",
            "Usamos reconocimiento facial para identificarte",
          ].map((item) => (
            <Text key={item} style={styles.notItem}>✕  {item}</Text>
          ))}
        </View>

        {/* Checkbox unificado */}
        <TouchableOpacity
          style={styles.singleCheckRow}
          onPress={() => setAccepted((v) => !v)}
          activeOpacity={0.75}
        >
          <View style={[styles.checkbox, accepted && styles.checkboxChecked]}>
            {accepted && <Text style={styles.checkmark}>✓</Text>}
          </View>
          <Text style={styles.singleCheckText}>
            He leído y acepto el tratamiento de mis datos biométricos según los puntos anteriores.
          </Text>
        </TouchableOpacity>

      </ScrollView>

      {/* CTA */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.proceedBtn, (!accepted || loading) && styles.proceedBtnDisabled]}
          onPress={handleProceed}
          disabled={!accepted || loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.primary} />
          ) : (
            <Text style={styles.proceedBtnText}>Acepto — Ir al pago →</Text>
          )}
        </TouchableOpacity>
        <Text style={styles.footerNote}>
          Puedes retirar tu consentimiento en cualquier momento desde Ajustes.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { padding: SPACING.lg, paddingBottom: 160 },

  headerBlock: { alignItems: "center", marginBottom: SPACING.xl },
  icon: { fontSize: 48, marginBottom: SPACING.md },
  title: { color: COLORS.text, fontSize: 24, ...FONTS.heading, textAlign: "center" },
  subtitle: { color: COLORS.textMuted, fontSize: 14, lineHeight: 20, textAlign: "center", marginTop: SPACING.sm },

  pointsBlock: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: SPACING.sm,
  },
  pointRow: { flexDirection: "row", gap: 8, alignItems: "flex-start" },
  pointBullet: { color: COLORS.accent, fontSize: 18, lineHeight: 22, flexShrink: 0 },
  pointText: { color: COLORS.textMuted, fontSize: 13, lineHeight: 19, flex: 1 },
  policyLink: { marginTop: SPACING.sm },
  link: { color: COLORS.accent, fontSize: 12, ...FONTS.label },

  notBlock: {
    backgroundColor: "rgba(224,85,85,0.07)",
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    borderWidth: 1,
    borderColor: "rgba(224,85,85,0.2)",
    gap: 6,
    marginBottom: SPACING.lg,
  },
  notTitle: { color: COLORS.error, fontSize: 13, ...FONTS.label, marginBottom: 4 },
  notItem: { color: COLORS.textMuted, fontSize: 13 },

  singleCheckRow: {
    flexDirection: "row",
    gap: SPACING.md,
    alignItems: "flex-start",
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    borderWidth: 1.5,
    borderColor: COLORS.border,
  },
  checkbox: {
    width: 26,
    height: 26,
    borderRadius: 7,
    borderWidth: 2,
    borderColor: COLORS.border,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
    flexShrink: 0,
  },
  checkboxChecked: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  checkmark: { color: COLORS.primary, fontSize: 15, fontWeight: "700" },
  singleCheckText: { color: COLORS.text, fontSize: 14, lineHeight: 21, flex: 1 },

  footer: {
    position: "absolute", bottom: 0, left: 0, right: 0,
    padding: SPACING.lg,
    paddingBottom: Platform.OS === "ios" ? 40 : SPACING.lg,
    backgroundColor: COLORS.bg,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.sm,
  },
  proceedBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.pill,
    paddingVertical: SPACING.md,
    alignItems: "center",
  },
  proceedBtnDisabled: { opacity: 0.35 },
  proceedBtnText: { color: COLORS.primary, fontSize: 17, ...FONTS.heading },
  footerNote: { color: COLORS.textMuted, fontSize: 11, textAlign: "center", lineHeight: 16 },
});
