/**
 * VisualsScreen — Prueba virtual de corte
 *
 * Muestra 3 tabs (uno por corte recomendado). Dentro de cada tab:
 *   - 3 imágenes del usuario con ese corte desde ángulos distintos
 *     (Frontal · 3/4 izquierda · 3/4 derecha) en un scroll horizontal
 *   - Por qué se eligió ese corte (descripcion_favorece del informe)
 *   - 3 links de referencia para mostrar al barbero
 *
 * Flujo:
 *   1. Usuario selecciona foto (galería o cámara)
 *   2. POST /generate-visuals → 202 → polling cada 4s
 *   3. Cuando status=ready → muestra las 9 imágenes (3 cuts × 3 angles)
 */

import React, { useState, useCallback, useRef } from "react";
import {
  ActivityIndicator,
  Alert,
  Dimensions,
  FlatList,
  Image,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useRoute, useNavigation } from "@react-navigation/native";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { api } from "../services/api";

const { width: SCREEN_W } = Dimensions.get("window");
const IMG_W = SCREEN_W - SPACING.lg * 2;
const IMG_H = IMG_W * 1.25;
const ANGLE_THUMB_W = (SCREEN_W - SPACING.lg * 2 - SPACING.sm * 2) / 3;

type AngleImage = {
  angle_id: string;
  label: string;
  url: string;
  error?: string;
};

type Visual = {
  cut_index: number;
  nombre_en: string;
  angles: AngleImage[];
  references: { search_query: string; source: string; nombre_en: string }[];
  has_any_image: boolean;
  error?: string;
};

type Cut = {
  nombre: string;
  nombre_tecnico: string;
  descripcion_favorece?: string;
  nivel_estilo?: string;
  nivel_mantenimiento?: string;
};

type Status = "idle" | "picking" | "uploading" | "processing" | "ready" | "failed";

const ANGLE_LABELS: Record<string, string> = {
  frontal: "Frontal",
  three_quarter_left: "3/4 Izq",
  three_quarter_right: "3/4 Der",
};

export default function VisualsScreen() {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const { analysisId, cuts = [] } = route.params as {
    analysisId: string;
    cuts: Cut[];
  };

  const [status, setStatus] = useState<Status>("idle");
  const [visuals, setVisuals] = useState<Visual[]>([]);
  const [activeTab, setActiveTab] = useState(0);
  const [activeAngle, setActiveAngle] = useState<Record<number, number>>({});
  const [pollCount, setPollCount] = useState(0);

  const currentVisual: Visual | undefined = visuals[activeTab];
  const currentCut: Cut | undefined = cuts[activeTab];

  const pickAndGenerate = useCallback(async () => {
    setStatus("picking");

    const choice = await new Promise<"camera" | "gallery" | "cancel">((resolve) => {
      Alert.alert(
        "Selecciona una foto frontal",
        "Buena iluminación y cara centrada dan mejores resultados.",
        [
          { text: "Cámara", onPress: () => resolve("camera") },
          { text: "Galería", onPress: () => resolve("gallery") },
          { text: "Cancelar", style: "cancel", onPress: () => resolve("cancel") },
        ]
      );
    });

    if (choice === "cancel") { setStatus("idle"); return; }

    let pickerResult;
    if (choice === "camera") {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) { Alert.alert("Permiso de cámara necesario."); setStatus("idle"); return; }
      pickerResult = await ImagePicker.launchCameraAsync({
        mediaTypes: ["images"], quality: 0.9, allowsEditing: true, aspect: [3, 4],
      });
    } else {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) { Alert.alert("Permiso de galería necesario."); setStatus("idle"); return; }
      pickerResult = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"], quality: 0.9, allowsEditing: true, aspect: [3, 4],
      });
    }

    if (pickerResult.canceled || !pickerResult.assets?.[0]) { setStatus("idle"); return; }

    setStatus("uploading");
    try {
      await api.generateVisuals(analysisId, pickerResult.assets[0].uri);
      setStatus("processing");
      setPollCount(0);
      setTimeout(() => poll(0), 5000);
    } catch (e: any) {
      Alert.alert("Error", e.message ?? "No se pudo iniciar la generación.");
      setStatus("failed");
    }
  }, [analysisId]);

  const poll = useCallback(async (attempt: number) => {
    if (attempt > 40) {
      setStatus("failed");
      Alert.alert("Tiempo agotado", "La generación tardó demasiado. Prueba con otra foto.");
      return;
    }
    try {
      const data = await api.getVisuals(analysisId);
      if (data.visuals_status === "ready") {
        setVisuals(data.visuals ?? []);
        setStatus("ready");
      } else if (data.visuals_status === "failed") {
        setStatus("failed");
        Alert.alert("Error de generación", "Intenta con una foto más clara y en primer plano.");
      } else {
        setPollCount(attempt + 1);
        setTimeout(() => poll(attempt + 1), 4000);
      }
    } catch {
      setTimeout(() => poll(attempt + 1), 5000);
    }
  }, [analysisId]);

  const getAngleIdx = (cutIdx: number) => activeAngle[cutIdx] ?? 0;
  const setAngleIdx = (cutIdx: number, idx: number) =>
    setActiveAngle((prev) => ({ ...prev, [cutIdx]: idx }));

  const openRef = (query: string) => {
    const url = `https://www.google.com/search?q=${encodeURIComponent(query + " men haircut")}&tbm=isch`;
    Linking.openURL(url);
  };

  const progressPct = Math.min(92, (pollCount / 12) * 100);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scroll}
      showsVerticalScrollIndicator={false}
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <View style={styles.header}>
        <Text style={styles.headerEyebrow}>PRUEBA VIRTUAL DE CORTE</Text>
        <Text style={styles.headerTitle}>Cómo quedarías</Text>
        <Text style={styles.headerSub}>
          IA genera 3 imágenes tuyas con cada corte recomendado{"\n"}
          desde ángulos distintos — frontal, 3/4 izquierda, 3/4 derecha.
        </Text>
      </View>

      {/* ── CTA / Loading ───────────────────────────────────────────── */}
      {(status === "idle" || status === "failed") && (
        <TouchableOpacity style={styles.startBtn} onPress={pickAndGenerate} activeOpacity={0.85}>
          <Text style={styles.startBtnText}>
            {status === "failed" ? "Reintentar con otra foto" : "Seleccionar foto frontal"}
          </Text>
          <View style={styles.startBtnArrow}>
            <Text style={styles.startBtnArrowText}>→</Text>
          </View>
        </TouchableOpacity>
      )}

      {(status === "uploading" || status === "picking") && (
        <View style={styles.loadingCard}>
          <ActivityIndicator size="large" color={COLORS.accent} />
          <Text style={styles.loadingTitle}>Subiendo foto…</Text>
        </View>
      )}

      {status === "processing" && (
        <View style={styles.loadingCard}>
          <ActivityIndicator size="large" color={COLORS.accent} />
          <Text style={styles.loadingTitle}>Generando 9 imágenes…</Text>
          <Text style={styles.loadingSubtitle}>
            3 cortes × 3 ángulos — unos 40-60 segundos
          </Text>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${progressPct}%` }]} />
          </View>
          <Text style={styles.loadingStep}>
            {pollCount < 4 ? "Procesando foto…" :
             pollCount < 8 ? "Generando vistas frontales…" :
             pollCount < 12 ? "Añadiendo perspectivas…" :
             "Finalizando…"}
          </Text>
        </View>
      )}

      {/* ── Cut tabs ────────────────────────────────────────────────── */}
      <View style={styles.tabBar}>
        {(cuts.length ? cuts : [{nombre: "Corte 1", nombre_tecnico: ""}, {nombre: "Corte 2", nombre_tecnico: ""}, {nombre: "Corte 3", nombre_tecnico: ""}]).slice(0, 3).map((cut, i) => (
          <TouchableOpacity
            key={i}
            style={[styles.tab, activeTab === i && styles.tabActive]}
            onPress={() => setActiveTab(i)}
            activeOpacity={0.75}
          >
            <Text style={[styles.tabIndex, activeTab === i && styles.tabIndexActive]}>{i + 1}</Text>
            <Text style={[styles.tabLabel, activeTab === i && styles.tabLabelActive]} numberOfLines={2}>
              {cut.nombre_tecnico || cut.nombre}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* ── Cut detail ─────────────────────────────────────────────── */}
      <View style={styles.cutDetail}>

        {/* Why this cut */}
        {currentCut?.descripcion_favorece ? (
          <View style={styles.whyBox}>
            <Text style={styles.whyLabel}>POR QUÉ ESTE CORTE TE FAVORECE</Text>
            <Text style={styles.whyText}>{currentCut.descripcion_favorece}</Text>
            {currentCut.nivel_estilo && (
              <View style={styles.tagRow}>
                <View style={styles.tag}><Text style={styles.tagText}>{currentCut.nivel_estilo}</Text></View>
                <View style={styles.tag}><Text style={styles.tagText}>{currentCut.nivel_mantenimiento}</Text></View>
              </View>
            )}
          </View>
        ) : null}

        {/* Images — ready state */}
        {status === "ready" && currentVisual?.angles?.length > 0 && (
          <View style={styles.imagesBlock}>
            {/* Main image (selected angle) */}
            <AngleImageView
              angle={currentVisual.angles[getAngleIdx(activeTab)]}
              style={styles.mainImage}
            />

            {/* Angle selector thumbnails */}
            <View style={styles.thumbRow}>
              {currentVisual.angles.map((angle, ai) => (
                <TouchableOpacity
                  key={ai}
                  style={[styles.thumb, getAngleIdx(activeTab) === ai && styles.thumbActive]}
                  onPress={() => setAngleIdx(activeTab, ai)}
                  activeOpacity={0.8}
                >
                  {angle.url ? (
                    <Image source={{ uri: angle.url }} style={styles.thumbImg} resizeMode="cover" />
                  ) : (
                    <View style={[styles.thumbImg, styles.thumbEmpty]}>
                      <Text style={styles.thumbEmptyIcon}>✕</Text>
                    </View>
                  )}
                  <Text style={[styles.thumbLabel, getAngleIdx(activeTab) === ai && styles.thumbLabelActive]}>
                    {ANGLE_LABELS[angle.angle_id] ?? angle.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Images — processing placeholder */}
        {status === "processing" && (
          <View style={styles.imagePlaceholder}>
            <ActivityIndicator color={COLORS.accent} />
            <Text style={styles.imagePlaceholderText}>Generando imágenes…</Text>
          </View>
        )}

        {/* References */}
        {currentVisual?.references?.length > 0 || currentCut ? (
          <View style={styles.refBlock}>
            <Text style={styles.refBlockTitle}>REFERENCIAS PARA TU BARBERO</Text>
            <Text style={styles.refBlockSub}>Abre en Google Imágenes y muéstraselas</Text>
            {(currentVisual?.references ?? buildFallbackRefs(currentCut)).map((ref, i) => (
              <TouchableOpacity
                key={i}
                style={styles.refRow}
                onPress={() => openRef(ref.search_query)}
                activeOpacity={0.8}
              >
                <Text style={styles.refIcon}>🔍</Text>
                <Text style={styles.refText}>{ref.search_query}</Text>
                <Text style={styles.refArrow}>→</Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : null}
      </View>

      {/* ── GDPR footnote ───────────────────────────────────────────── */}
      <Text style={styles.gdprNote}>
        La foto que envías no se almacena. Las imágenes generadas son sintéticas y expiran en 24h.
      </Text>
    </ScrollView>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function AngleImageView({ angle, style }: { angle: AngleImage; style: any }) {
  const [errored, setErrored] = useState(false);

  if (!angle.url || errored) {
    return (
      <View style={[style, styles.imgError]}>
        <Text style={styles.imgErrorText}>
          {angle.error ? "No se pudo generar" : "Imagen no disponible"}
        </Text>
      </View>
    );
  }

  return (
    <Image
      source={{ uri: angle.url }}
      style={style}
      resizeMode="cover"
      onError={() => setErrored(true)}
    />
  );
}


function buildFallbackRefs(cut?: Cut): { search_query: string; source: string; nombre_en: string }[] {
  if (!cut) return [];
  const name = cut.nombre_tecnico || cut.nombre;
  return [
    { search_query: `${name} men haircut`, source: "fallback", nombre_en: name },
    { search_query: `${name} barbershop result`, source: "fallback", nombre_en: name },
    { search_query: `${name} how to ask barber`, source: "fallback", nombre_en: name },
  ];
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg },
  scroll: { paddingBottom: 80 },

  header: {
    padding: SPACING.lg,
    paddingTop: Platform.OS === "ios" ? SPACING.xl : SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    gap: SPACING.sm,
  },
  headerEyebrow: { color: COLORS.accent, fontSize: 10, letterSpacing: 3, fontWeight: "700" as const },
  headerTitle: { color: COLORS.text, fontSize: 30, ...FONTS.heading },
  headerSub: { color: COLORS.textMuted, fontSize: 13, lineHeight: 19 },

  startBtn: {
    margin: SPACING.lg,
    backgroundColor: COLORS.accent,
    borderRadius: RADIUS.md,
    paddingVertical: SPACING.md + 4,
    paddingLeft: SPACING.lg,
    paddingRight: SPACING.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  startBtnText: { color: COLORS.primary, fontSize: 17, ...FONTS.heading },
  startBtnArrow: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: "rgba(0,0,0,0.18)",
    alignItems: "center", justifyContent: "center",
  },
  startBtnArrowText: { color: COLORS.primary, fontSize: 18, fontWeight: "700" as const },

  loadingCard: {
    margin: SPACING.lg,
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.xl,
    alignItems: "center",
    gap: SPACING.md,
  },
  loadingTitle: { color: COLORS.text, fontSize: 17, ...FONTS.heading },
  loadingSubtitle: { color: COLORS.textMuted, fontSize: 13, textAlign: "center" },
  progressTrack: {
    width: "100%", height: 4,
    backgroundColor: COLORS.border, borderRadius: 2, overflow: "hidden",
  },
  progressFill: { height: "100%", backgroundColor: COLORS.accent, borderRadius: 2 },
  loadingStep: { color: COLORS.textMuted, fontSize: 12 },

  tabBar: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    marginTop: SPACING.sm,
  },
  tab: {
    flex: 1,
    paddingVertical: SPACING.sm + 4,
    paddingHorizontal: SPACING.sm,
    alignItems: "center",
    borderBottomWidth: 2.5,
    borderBottomColor: "transparent",
    gap: 4,
  },
  tabActive: { borderBottomColor: COLORS.accent },
  tabIndex: {
    width: 22, height: 22, borderRadius: 11,
    backgroundColor: COLORS.border,
    textAlign: "center",
    color: COLORS.textMuted,
    fontSize: 12, fontWeight: "700" as const,
    lineHeight: 22,
  },
  tabIndexActive: { backgroundColor: COLORS.accent, color: COLORS.primary },
  tabLabel: { color: COLORS.textMuted, fontSize: 10, textAlign: "center", ...FONTS.label },
  tabLabelActive: { color: COLORS.accent },

  cutDetail: { padding: SPACING.lg, gap: SPACING.xl },

  whyBox: {
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
    padding: SPACING.md,
    gap: SPACING.sm,
  },
  whyLabel: { color: COLORS.accent, fontSize: 9, letterSpacing: 2, fontWeight: "700" as const },
  whyText: { color: COLORS.text, fontSize: 14, lineHeight: 21 },
  tagRow: { flexDirection: "row", gap: SPACING.sm, marginTop: 2 },
  tag: {
    backgroundColor: COLORS.border, borderRadius: RADIUS.pill,
    paddingHorizontal: SPACING.sm, paddingVertical: 3,
  },
  tagText: { color: COLORS.textMuted, fontSize: 11, ...FONTS.label },

  imagesBlock: { gap: SPACING.md },
  mainImage: {
    width: IMG_W, height: IMG_H,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.surface,
  },
  imgError: {
    alignItems: "center", justifyContent: "center",
    backgroundColor: COLORS.surface,
  },
  imgErrorText: { color: COLORS.textMuted, fontSize: 13 },

  thumbRow: { flexDirection: "row", gap: SPACING.sm },
  thumb: {
    flex: 1,
    borderRadius: RADIUS.sm,
    overflow: "hidden",
    borderWidth: 2,
    borderColor: "transparent",
    gap: 4,
  },
  thumbActive: { borderColor: COLORS.accent },
  thumbImg: {
    width: "100%", aspectRatio: 3 / 4,
    backgroundColor: COLORS.surface,
  },
  thumbEmpty: { alignItems: "center", justifyContent: "center" },
  thumbEmptyIcon: { color: COLORS.textMuted, fontSize: 14 },
  thumbLabel: { color: COLORS.textMuted, fontSize: 10, textAlign: "center", ...FONTS.label, paddingBottom: 4 },
  thumbLabelActive: { color: COLORS.accent },

  imagePlaceholder: {
    height: IMG_H * 0.5,
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.md,
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.md,
  },
  imagePlaceholderText: { color: COLORS.textMuted, fontSize: 13 },

  refBlock: { gap: SPACING.sm },
  refBlockTitle: { color: COLORS.textMuted, fontSize: 9, letterSpacing: 2, fontWeight: "700" as const },
  refBlockSub: { color: COLORS.textMuted, fontSize: 12, marginBottom: 4 },
  refRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.sm,
    backgroundColor: COLORS.surface,
    borderRadius: RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SPACING.sm + 2,
  },
  refIcon: { fontSize: 14 },
  refText: { color: COLORS.accent, fontSize: 13, flex: 1, lineHeight: 18 },
  refArrow: { color: COLORS.textMuted, fontSize: 12 },

  gdprNote: {
    color: COLORS.textMuted, fontSize: 11, lineHeight: 16,
    textAlign: "center",
    marginHorizontal: SPACING.lg,
    marginTop: SPACING.lg,
  },
});
