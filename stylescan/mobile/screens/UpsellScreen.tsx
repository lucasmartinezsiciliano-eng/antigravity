import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { api } from "../services/api";

const COLORIMETRY_FEATURES = [
  "Paleta de colores que mejor sientan a tu tono de piel",
  "Colores de ropa que refuerzan tu imagen",
  "Tonos de pelo recomendados (si quieres teñirte)",
  "Gafas que equilibran tu forma facial",
];

const PRODUCTS_FEATURES = [
  "Productos exactos para tu textura y densidad",
  "Rutina de mantenimiento paso a paso",
  "Técnica de aplicación y cantidad",
  "Qué evitar según tu tipo de cabello",
];

export default function UpsellScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { analysisId, type } = route.params as { analysisId: string; type: "colorimetry" | "products" | "pack" };

  const [loading, setLoading] = useState(false);
  const [waitingPayment, setWaitingPayment] = useState(false);

  const isColorimetry = type === "colorimetry";
  const features = isColorimetry ? COLORIMETRY_FEATURES : PRODUCTS_FEATURES;

  const handlePurchase = async () => {
    setLoading(true);
    try {
      const data = await api.purchaseUpsell(analysisId, type);
      setLoading(false);

      // Dev mode: direct skip, no browser needed
      if (data.checkout_url.includes("dev-upsell-skipped")) {
        navigation.goBack();
        return;
      }

      // Open Stripe checkout in browser
      await Linking.openURL(data.checkout_url);
      setWaitingPayment(true);
    } catch (e: any) {
      setLoading(false);
      if (e.message?.includes("409") || e.message?.toLowerCase().includes("ya tienes")) {
        Alert.alert("Ya incluido", "Este extra ya está incluido en tu análisis.", [
          { text: "Ver resultado", onPress: () => navigation.goBack() },
        ]);
      } else {
        Alert.alert("Error", e.message ?? "No se pudo iniciar el pago. Inténtalo de nuevo.");
      }
    }
  };

  const handleBackToResults = () => {
    navigation.goBack();
  };

  if (waitingPayment) {
    return (
      <View style={styles.waitingContainer}>
        <Text style={styles.waitingIcon}>💳</Text>
        <Text style={styles.waitingTitle}>Completa el pago</Text>
        <Text style={styles.waitingSubtitle}>
          Finaliza el pago en el navegador y vuelve aquí.{"\n"}
          Tu análisis se actualizará automáticamente.
        </Text>
        <TouchableOpacity style={styles.ctaBtn} onPress={handleBackToResults}>
          <Text style={styles.ctaBtnText}>Ya he pagado — Ver resultado →</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.skipBtn} onPress={() => setWaitingPayment(false)}>
          <Text style={styles.skipBtnText}>Volver atrás</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
      <View style={styles.hero}>
        <Text style={styles.icon}>{isColorimetry ? "🎨" : "🧴"}</Text>
        <Text style={styles.title}>
          {isColorimetry ? "Colorimetría personalizada" : "Guía de productos"}
        </Text>
        <Text style={styles.subtitle}>
          {isColorimetry
            ? "Descubre qué colores favorecen más a tu piel, rasgos y forma facial específica."
            : "Los productos exactos para tu cabello y el corte que te hemos recomendado."}
        </Text>
      </View>

      <View style={styles.priceBox}>
        <Text style={styles.price}>2,49 €</Text>
        <Text style={styles.priceNote}>Pago único · Resultado en segundos</Text>
      </View>

      <View style={styles.featuresBlock}>
        {features.map((f) => (
          <View key={f} style={styles.featureRow}>
            <Text style={styles.featureCheck}>✓</Text>
            <Text style={styles.featureText}>{f}</Text>
          </View>
        ))}
      </View>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.ctaBtn, loading && styles.ctaBtnDisabled]}
          onPress={handlePurchase}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.primary} />
          ) : (
            <Text style={styles.ctaBtnText}>Añadir por 2,49 € →</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity style={styles.skipBtn} onPress={handleBackToResults}>
          <Text style={styles.skipBtnText}>Ahora no</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  scroll: {
    padding: SPACING.lg,
    paddingBottom: Platform.OS === "ios" ? 50 : SPACING.xl,
  },

  hero: { alignItems: "center", marginBottom: SPACING.xl, paddingTop: SPACING.md },
  icon: { fontSize: 64, marginBottom: SPACING.md },
  title: { color: COLORS.text, fontSize: 24, ...FONTS.heading, textAlign: "center", marginBottom: SPACING.sm },
  subtitle: { color: COLORS.textMuted, fontSize: 15, lineHeight: 22, textAlign: "center" },

  priceBox: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderWidth: 1.5,
    borderColor: COLORS.accent,
    padding: SPACING.lg,
    alignItems: "center",
    marginBottom: SPACING.xl,
  },
  price: { color: COLORS.accent, fontSize: 40, ...FONTS.heading },
  priceNote: { color: COLORS.textMuted, fontSize: 13, marginTop: 4 },

  featuresBlock: { gap: SPACING.md, marginBottom: SPACING.xl },
  featureRow: { flexDirection: "row", gap: SPACING.md, alignItems: "flex-start" },
  featureCheck: { color: COLORS.success, fontSize: 16, ...FONTS.label, width: 20, textAlign: "center" },
  featureText: { color: COLORS.text, fontSize: 15, lineHeight: 22, flex: 1 },

  footer: { gap: SPACING.sm },
  ctaBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.pill,
    paddingVertical: SPACING.md,
    alignItems: "center",
  },
  ctaBtnDisabled: { opacity: 0.6 },
  ctaBtnText: { color: COLORS.primary, fontSize: 17, ...FONTS.heading },
  skipBtn: { alignItems: "center", paddingVertical: SPACING.sm },
  skipBtnText: { color: COLORS.textMuted, fontSize: 14 },

  waitingContainer: {
    flex: 1,
    backgroundColor: COLORS.bg,
    alignItems: "center",
    justifyContent: "center",
    padding: SPACING.xl,
    gap: SPACING.lg,
  },
  waitingIcon: { fontSize: 72 },
  waitingTitle: { color: COLORS.text, fontSize: 24, ...FONTS.heading, textAlign: "center" },
  waitingSubtitle: { color: COLORS.textMuted, fontSize: 15, lineHeight: 24, textAlign: "center" },
});
