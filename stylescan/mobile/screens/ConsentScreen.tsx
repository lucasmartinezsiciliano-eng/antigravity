/**
 * ConsentScreen — RGPD Art. 9 explicit consent
 * Each checkbox must be actively ticked — no pre-checked boxes (AEPD requirement).
 * The exact consent text shown is hashed and sent to the backend for audit.
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

// This text is hashed — changing it changes the hash stored in the audit log.
const CONSENT_TEXT_V1 = `StyleScan trata tus fotos del rostro para extraer 468 puntos de medición facial (datos biométricos, Categoría Especial RGPD Art. 9). Las fotos originales se borran inmediatamente tras el análisis. Solo se guardan métricas numéricas durante 90 días. Tienes derecho de acceso, rectificación, supresión y portabilidad. Puedes retirar este consentimiento en cualquier momento. Responsable: StyleScan SL. Contacto DPD: privacidad@stylescan.app.`;

interface ConsentItem {
  key: keyof ConsentState;
  text: string;
  required: boolean;
}

interface ConsentState {
  biometric: boolean;
  special_category: boolean;
  retention_90d: boolean;
  photo_deletion: boolean;
  age: boolean;
}

const CONSENT_ITEMS: ConsentItem[] = [
  {
    key: "biometric",
    text: "Consiento que StyleScan procese mis fotos del rostro para extraer mediciones faciales (datos biométricos).",
    required: true,
  },
  {
    key: "special_category",
    text: "Entiendo que mis datos biométricos son Categoría Especial bajo el RGPD (Art. 9) y que este consentimiento es voluntario.",
    required: true,
  },
  {
    key: "photo_deletion",
    text: "Entiendo que mis fotos originales se eliminan automáticamente e inmediatamente tras el análisis y no se almacenan.",
    required: true,
  },
  {
    key: "retention_90d",
    text: "Acepto que las métricas numéricas derivadas (no las fotos) se conserven durante 90 días para permitir que acceda a mi informe.",
    required: true,
  },
  {
    key: "age",
    text: "Confirmo que soy mayor de 18 años.",
    required: true,
  },
];

export default function ConsentScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { quizAnswers, barberCode } = route.params;

  const [consent, setConsent] = useState<ConsentState>({
    biometric: false,
    special_category: false,
    retention_90d: false,
    photo_deletion: false,
    age: false,
  });
  const [loading, setLoading] = useState(false);

  const allChecked = Object.values(consent).every(Boolean);

  const toggle = (key: keyof ConsentState) => {
    setConsent((c) => ({ ...c, [key]: !c[key] }));
  };

  const handleProceed = async () => {
    if (!allChecked) return;
    setLoading(true);

    try {
      // 1. Create analysis + get checkout URL
      const initResult = await api.initiateAnalysis({
        barber_code: barberCode ?? undefined,
        quiz_answers: quizAnswers,
      });

      const { analysis_id, checkout_url } = initResult;
      await storage.saveAnalysisId(analysis_id);

      // 2. Hash the consent text shown (RGPD audit trail)
      const consentHash = await Crypto.digestStringAsync(
        Crypto.CryptoDigestAlgorithm.SHA256,
        CONSENT_TEXT_V1
      );

      // 3. Record consent
      await api.recordConsent(analysis_id, {
        consented_biometric_processing: consent.biometric,
        consented_special_category_data: consent.special_category,
        consented_retention_90_days: consent.retention_90d,
        consented_immediate_photo_deletion: consent.photo_deletion,
        consented_age_verification: consent.age,
        consent_text_hash: consentHash,
      });

      // 4. Open Stripe checkout in browser
      const canOpen = await Linking.canOpenURL(checkout_url);
      if (canOpen) {
        await Linking.openURL(checkout_url);
        // After payment, user comes back to the app via deep link → Capture screen
        // Navigation will be handled by the deep link handler in App.tsx
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

        {/* Consent text block */}
        <View style={styles.legalBlock}>
          <Text style={styles.legalText}>{CONSENT_TEXT_V1}</Text>
          <TouchableOpacity onPress={() => Linking.openURL("https://stylescan.app/privacidad")}>
            <Text style={styles.link}>Leer política de privacidad completa →</Text>
          </TouchableOpacity>
        </View>

        {/* Checkboxes */}
        <View style={styles.checkboxes}>
          {CONSENT_ITEMS.map((item) => (
            <TouchableOpacity
              key={item.key}
              style={styles.checkboxRow}
              onPress={() => toggle(item.key)}
              activeOpacity={0.75}
            >
              <View style={[styles.checkbox, consent[item.key] && styles.checkboxChecked]}>
                {consent[item.key] && <Text style={styles.checkmark}>✓</Text>}
              </View>
              <Text style={styles.checkboxText}>{item.text}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* What we do NOT do */}
        <View style={styles.notBlock}>
          <Text style={styles.notTitle}>Lo que NUNCA hacemos:</Text>
          {[
            "Guardamos tus fotos originales",
            "Usamos tus datos para publicidad",
            "Compartimos tus datos con terceros",
            "Usamos reconocimiento facial para identificarte",
          ].map((item) => (
            <Text key={item} style={styles.notItem}>
              ✕  {item}
            </Text>
          ))}
        </View>
      </ScrollView>

      {/* CTA */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.proceedBtn, (!allChecked || loading) && styles.proceedBtnDisabled]}
          onPress={handleProceed}
          disabled={!allChecked || loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.primary} />
          ) : (
            <Text style={styles.proceedBtnText}>Acepto — Ir al pago →</Text>
          )}
        </TouchableOpacity>
        <Text style={styles.footerNote}>
          Todos los casillas son obligatorias. Puedes retirar tu consentimiento en cualquier momento desde Ajustes.
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

  legalBlock: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  legalText: { color: COLORS.textMuted, fontSize: 12, lineHeight: 18, marginBottom: SPACING.sm },
  link: { color: COLORS.accent, fontSize: 12, ...FONTS.label },

  checkboxes: { gap: SPACING.md, marginBottom: SPACING.lg },
  checkboxRow: { flexDirection: "row", gap: SPACING.md, alignItems: "flex-start" },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: COLORS.border,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
    flexShrink: 0,
  },
  checkboxChecked: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
  checkmark: { color: COLORS.primary, fontSize: 14, fontWeight: "700" },
  checkboxText: { color: COLORS.text, fontSize: 14, lineHeight: 20, flex: 1 },

  notBlock: {
    backgroundColor: "rgba(224,85,85,0.07)",
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    borderWidth: 1,
    borderColor: "rgba(224,85,85,0.2)",
    gap: 6,
  },
  notTitle: { color: COLORS.error, fontSize: 13, ...FONTS.label, marginBottom: 4 },
  notItem: { color: COLORS.textMuted, fontSize: 13 },

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
