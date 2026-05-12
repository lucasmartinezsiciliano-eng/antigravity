/**
 * ResultScreen — Display the full analysis report
 * Sections: facial summary, cranial proportions, 3 haircut cards,
 * cuts to avoid, specific tips, upsell CTA.
 */

import React, { useEffect, useState, useCallback } from "react";
import {
  ActivityIndicator,
  Alert,
  Clipboard,
  Platform,
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { api, AnalysisResult, HaircutRecommendation } from "../services/api";

const MAINTENANCE_LABELS: Record<string, string> = {
  bajo: "🟢 Mantenimiento bajo",
  medio: "🟡 Mantenimiento medio",
  alto: "🔴 Mantenimiento alto",
};

const FACE_SHAPE_ES: Record<string, string> = {
  oval: "Ovalada",
  round: "Redonda",
  square: "Cuadrada",
  oblong: "Alargada",
  heart: "Corazón",
  diamond: "Diamante",
  triangle: "Triangular",
};

export default function ResultScreen() {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const { analysisId } = route.params;

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);
  const [expandedCut, setExpandedCut] = useState<number | null>(0);

  const fetchResult = useCallback(async () => {
    try {
      const data = await api.getResult(analysisId);
      setResult(data);
      setLoading(false);
      setPolling(false);
    } catch (e: any) {
      if (e.message?.includes("202")) {
        // Still processing — keep polling
        setPolling(true);
        setTimeout(fetchResult, 3000);
      } else if (e.message?.includes("402")) {
        Alert.alert("Pago pendiente", "Completa el pago para ver el análisis.");
        navigation.goBack();
      } else {
        Alert.alert("Error", e.message ?? "No se pudo cargar el análisis.");
        setLoading(false);
      }
    }
  }, [analysisId, navigation]);

  useEffect(() => { fetchResult(); }, [fetchResult]);

  const handleShare = async () => {
    if (!result) return;
    try {
      await Share.share({
        message: `Acabo de descubrir que tengo la cara ${FACE_SHAPE_ES[result.face_shape] ?? result.face_shape} con StyleScan 🔥 ¿Cuál es la tuya? stylescan.app`,
        title: "Mi análisis de StyleScan",
      });
    } catch { /* ignore */ }
  };

  const copyBarberInstructions = (cut: HaircutRecommendation) => {
    Clipboard.setString(cut.como_pedirlo_al_barbero);
    Alert.alert("Copiado ✓", "Instrucciones copiadas. Pégalas en un mensaje a tu barbero.");
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.accent} />
        <Text style={styles.loadingText}>
          {polling ? "Analizando tus fotos…\nEsto puede tardar unos segundos." : "Cargando…"}
        </Text>
      </View>
    );
  }

  if (!result) return null;

  const { report } = result;
  const faceShapeLabel = FACE_SHAPE_ES[result.face_shape] ?? result.face_shape;
  const confidencePct = Math.round(result.confidence * 100);
  const expiresAt = new Date(result.expires_at).toLocaleDateString("es-ES");

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scroll}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={polling} onRefresh={fetchResult} tintColor={COLORS.accent} />}
    >
      {/* ── Hero ─────────────────────────────────────────────────── */}
      <View style={styles.hero}>
        <Text style={styles.heroLabel}>Tu forma facial</Text>
        <Text style={styles.heroShape}>{faceShapeLabel}</Text>
        <View style={styles.metaRow}>
          <MetaBadge icon="📸" label={`${result.photos_analyzed} fotos`} />
          <MetaBadge icon="🎯" label={`Confianza ${confidencePct}%`} />
          <MetaBadge icon="⏳" label={`Hasta ${expiresAt}`} />
        </View>
        <TouchableOpacity style={styles.shareBtn} onPress={handleShare}>
          <Text style={styles.shareBtnText}>Compartir resultado 🔗</Text>
        </TouchableOpacity>
      </View>

      {/* ── Resumen facial ───────────────────────────────────────── */}
      <Section title="Análisis facial" icon="🔬">
        <Text style={styles.bodyText}>{report.resumen_facial}</Text>
      </Section>

      <Section title="Proporciones craneales" icon="📐">
        <Text style={styles.bodyText}>{report.proporciones_craneales}</Text>
        <View style={styles.asymmetryBar}>
          <Text style={styles.asymmetryLabel}>Simetría facial</Text>
          <View style={styles.asymmetryTrack}>
            <View
              style={[
                styles.asymmetryFill,
                { width: `${Math.max(5, 100 - result.asymmetry_score * 400)}%` },
              ]}
            />
          </View>
          <Text style={styles.asymmetryPct}>
            {result.asymmetry_score < 0.06 ? "Excelente" :
             result.asymmetry_score < 0.12 ? "Buena" :
             result.asymmetry_score < 0.20 ? "Normal" : "Notable"}
          </Text>
        </View>
      </Section>

      {/* ── Ventaja facial ───────────────────────────────────────── */}
      {report.ventaja_facial && (
        <Section title="Tu ventaja facial" icon="⭐">
          <Text style={styles.bodyText}>{report.ventaja_facial}</Text>
        </Section>
      )}

      {/* ── Cortes recomendados ──────────────────────────────────── */}
      <Section title="Tus 3 cortes ideales" icon="✂️">
        {report.cortes_recomendados?.map((cut, i) => (
          <HaircutCard
            key={i}
            cut={cut}
            index={i}
            expanded={expandedCut === i}
            onToggle={() => setExpandedCut(expandedCut === i ? null : i)}
            onCopyInstructions={() => copyBarberInstructions(cut)}
          />
        ))}
      </Section>

      {/* ── Cortes a evitar ──────────────────────────────────────── */}
      <Section title="Cortes a evitar" icon="🚫">
        {report.cortes_a_evitar?.map((item, i) => (
          <View key={i} style={styles.avoidItem}>
            <Text style={styles.avoidText}>• {item}</Text>
          </View>
        ))}
      </Section>

      {/* ── Consejos específicos ──────────────────────────────────── */}
      <Section title="Consejos para tu forma facial" icon="💡">
        <Text style={styles.bodyText}>{report.consejos_especificos}</Text>
      </Section>

      {/* ── Virtual try-on CTA ───────────────────────────────────── */}
      <TouchableOpacity
        style={styles.visualsCTA}
        onPress={() =>
          navigation.navigate("Visuals", {
            analysisId: result.analysis_id,
            cuts: report.cortes_recomendados ?? [],
          })
        }
        activeOpacity={0.85}
      >
        <View style={styles.visualsCTALeft}>
          <Text style={styles.visualsCTATitle}>Ver cómo quedarías ✨</Text>
          <Text style={styles.visualsCTASub}>
            IA genera una foto tuya con cada corte recomendado
          </Text>
        </View>
        <Text style={styles.visualsCTAArrow}>→</Text>
      </TouchableOpacity>

      {/* ── Upsell colorimetría ───────────────────────────────────── */}
      {!result.includes_colorimetry && (
        <View style={styles.upsellCard}>
          <Text style={styles.upsellTitle}>🎨 Colorimetría personalizada</Text>
          <Text style={styles.upsellText}>
            Descubre qué colores de ropa, gafas y tono de pelo favorecen más a tu piel y rasgos.
          </Text>
          <TouchableOpacity
            style={styles.upsellBtn}
            onPress={() => navigation.navigate("Upsell", { analysisId, type: "colorimetry" })}
          >
            <Text style={styles.upsellBtnText}>Añadir por 2,49 € →</Text>
          </TouchableOpacity>
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Section({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{icon}  {title}</Text>
      {children}
    </View>
  );
}

function MetaBadge({ icon, label }: { icon: string; label: string }) {
  return (
    <View style={styles.metaBadge}>
      <Text style={styles.metaBadgeText}>{icon} {label}</Text>
    </View>
  );
}

function HaircutCard({
  cut, index, expanded, onToggle, onCopyInstructions,
}: {
  cut: HaircutRecommendation;
  index: number;
  expanded: boolean;
  onToggle: () => void;
  onCopyInstructions: () => void;
}) {
  return (
    <View style={[styles.cutCard, expanded && styles.cutCardExpanded]}>
      <TouchableOpacity style={styles.cutHeader} onPress={onToggle} activeOpacity={0.8}>
        <View style={styles.cutIndex}>
          <Text style={styles.cutIndexText}>{index + 1}</Text>
        </View>
        <View style={styles.cutHeaderText}>
          <Text style={styles.cutName}>{cut.nombre}</Text>
          <Text style={styles.cutMeta}>
            {MAINTENANCE_LABELS[cut.nivel_mantenimiento] ?? cut.nivel_mantenimiento}
            {"  ·  "}
            {cut.nivel_estilo}
          </Text>
        </View>
        <Text style={styles.cutChevron}>{expanded ? "▲" : "▼"}</Text>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.cutBody}>
          <Text style={styles.cutBodyLabel}>¿Por qué te favorece?</Text>
          <Text style={styles.cutBodyText}>{cut.descripcion_favorece}</Text>

          <Text style={styles.cutBodyLabel}>Cómo pedirlo al barbero</Text>
          <View style={styles.barberBox}>
            <Text style={styles.barberBoxText}>{cut.como_pedirlo_al_barbero}</Text>
          </View>
          <TouchableOpacity style={styles.copyBtn} onPress={onCopyInstructions}>
            <Text style={styles.copyBtnText}>📋 Copiar instrucciones para el barbero</Text>
          </TouchableOpacity>

          <Text style={styles.cutBodyLabel}>Mantenimiento en casa</Text>
          <Text style={styles.cutBodyText}>{cut.mantenimiento_casa}</Text>

          <Text style={styles.cutBodyLabel}>Frecuencia de visita</Text>
          <Text style={styles.cutBodyText}>{cut.frecuencia_barberia}</Text>
        </View>
      )}
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { paddingBottom: 60 },
  loadingContainer: { flex: 1, backgroundColor: COLORS.bg, alignItems: "center", justifyContent: "center", gap: SPACING.lg },
  loadingText: { color: COLORS.textMuted, textAlign: "center", lineHeight: 22 },

  // Hero
  hero: {
    backgroundColor: COLORS.surface,
    padding: SPACING.xl,
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  heroLabel: { color: COLORS.textMuted, fontSize: 13, ...FONTS.label, letterSpacing: 2, textTransform: "uppercase" },
  heroShape: { color: COLORS.accent, fontSize: 42, ...FONTS.heading, marginVertical: SPACING.sm },
  metaRow: { flexDirection: "row", gap: SPACING.sm, flexWrap: "wrap", justifyContent: "center", marginBottom: SPACING.md },
  metaBadge: { backgroundColor: COLORS.border, borderRadius: RADIUS.pill, paddingHorizontal: SPACING.sm, paddingVertical: 4 },
  metaBadgeText: { color: COLORS.textMuted, fontSize: 12, ...FONTS.label },
  shareBtn: { borderWidth: 1.5, borderColor: COLORS.accent, borderRadius: RADIUS.pill, paddingHorizontal: SPACING.lg, paddingVertical: SPACING.sm },
  shareBtnText: { color: COLORS.accent, fontSize: 14, ...FONTS.label },

  // Sections
  section: { padding: SPACING.lg, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  sectionTitle: { color: COLORS.text, fontSize: 18, ...FONTS.heading, marginBottom: SPACING.md },
  bodyText: { color: COLORS.textMuted, fontSize: 15, lineHeight: 22 },

  // Asymmetry bar
  asymmetryBar: { marginTop: SPACING.md, gap: 6 },
  asymmetryLabel: { color: COLORS.textMuted, fontSize: 12, ...FONTS.label },
  asymmetryTrack: { height: 6, backgroundColor: COLORS.border, borderRadius: 3, overflow: "hidden" },
  asymmetryFill: { height: "100%", backgroundColor: COLORS.success, borderRadius: 3 },
  asymmetryPct: { color: COLORS.success, fontSize: 12, ...FONTS.label },

  // Haircut cards
  cutCard: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    marginBottom: SPACING.sm,
    overflow: "hidden",
  },
  cutCardExpanded: { borderColor: COLORS.accent },
  cutHeader: { flexDirection: "row", alignItems: "center", padding: SPACING.md, gap: SPACING.md },
  cutIndex: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: COLORS.accent,
    alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
  cutIndexText: { color: COLORS.primary, fontSize: 15, ...FONTS.heading },
  cutHeaderText: { flex: 1 },
  cutName: { color: COLORS.text, fontSize: 16, ...FONTS.label },
  cutMeta: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },
  cutChevron: { color: COLORS.textMuted, fontSize: 12 },

  cutBody: { padding: SPACING.md, paddingTop: 0, gap: SPACING.sm },
  cutBodyLabel: { color: COLORS.accent, fontSize: 12, ...FONTS.label, marginTop: SPACING.sm, textTransform: "uppercase", letterSpacing: 0.8 },
  cutBodyText: { color: COLORS.textMuted, fontSize: 14, lineHeight: 20 },
  barberBox: {
    backgroundColor: COLORS.bg,
    borderRadius: RADIUS.sm,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
    padding: SPACING.sm,
  },
  barberBoxText: { color: COLORS.text, fontSize: 14, lineHeight: 20, fontStyle: "italic" },
  copyBtn: { borderWidth: 1, borderColor: COLORS.border, borderRadius: RADIUS.sm, padding: SPACING.sm, alignItems: "center" },
  copyBtnText: { color: COLORS.accent, fontSize: 13, ...FONTS.label },

  // Avoid
  avoidItem: { paddingVertical: 4 },
  avoidText: { color: COLORS.textMuted, fontSize: 14, lineHeight: 20 },

  // Virtual try-on CTA
  visualsCTA: {
    margin: SPACING.lg,
    backgroundColor: "rgba(201,168,76,0.12)",
    borderRadius: RADIUS.md,
    borderWidth: 1.5,
    borderColor: COLORS.accent,
    padding: SPACING.lg,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  visualsCTALeft: { flex: 1, gap: 4 },
  visualsCTATitle: { color: COLORS.accent, fontSize: 17, ...FONTS.heading },
  visualsCTASub: { color: COLORS.textMuted, fontSize: 13, lineHeight: 18 },
  visualsCTAArrow: { color: COLORS.accent, fontSize: 22, marginLeft: SPACING.sm },

  // Upsell
  upsellCard: {
    margin: SPACING.lg,
    backgroundColor: "rgba(201,168,76,0.08)",
    borderRadius: RADIUS.md,
    borderWidth: 1.5,
    borderColor: COLORS.accent,
    padding: SPACING.lg,
    gap: SPACING.sm,
  },
  upsellTitle: { color: COLORS.accent, fontSize: 17, ...FONTS.heading },
  upsellText: { color: COLORS.textMuted, fontSize: 14, lineHeight: 20 },
  upsellBtn: {
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.pill,
    paddingVertical: SPACING.sm,
    alignItems: "center",
    marginTop: SPACING.sm,
  },
  upsellBtnText: { color: COLORS.primary, fontSize: 15, ...FONTS.heading },
});
