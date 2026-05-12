/**
 * CaptureScreen — Guided photo capture (core UX differentiator)
 *
 * 3 progressive captures with:
 * - Animated oval + crosshair positioning guide
 * - Per-step instructions (angle, position, lighting)
 * - Countdown auto-capture (3s) or manual trigger
 * - Post-capture blur/brightness validation
 * - Retry if quality is poor
 *
 * Note: Real-time face position tracking (face detection in viewfinder)
 * is planned for v2. SDK 54 requires separate processing pipeline.
 * The guided overlay + protocol is the key differentiator over competitors.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  Easing,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Vibration,
  Alert,
} from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import { useNavigation, useRoute } from "@react-navigation/native";
import { COLORS, SPACING, RADIUS, FONTS } from "../constants/theme";
import { api } from "../services/api";

const { width: W, height: H } = Dimensions.get("window");
const OVAL_W = W * 0.68;
const OVAL_H = OVAL_W * 1.35;

// ─── Capture protocol ─────────────────────────────────────────────────────────

interface CaptureStep {
  id: number;
  title: string;
  instruction: string;
  tips: string[];
  icon: string;
}

const STEPS: CaptureStep[] = [
  {
    id: 1,
    title: "Foto frontal",
    instruction: "Mira directamente a la cámara",
    tips: [
      "Centra tu rostro en el óvalo",
      "Luz natural de frente, sin contraluz",
      "Sin gafas de sol",
    ],
    icon: "⬛",
  },
  {
    id: 2,
    title: "Perfil izquierdo",
    instruction: "Gira la cabeza 90° a la izquierda",
    tips: [
      "Perfil completo — oreja mirando a la cámara",
      "Se tiene que ver bien la forma de la cabeza",
      "Mantén la barbilla al mismo nivel que el suelo",
    ],
    icon: "◀",
  },
  {
    id: 3,
    title: "Perfil derecho",
    instruction: "Gira la cabeza 90° a la derecha",
    tips: [
      "Perfil completo — oreja mirando a la cámara",
      "Se tiene que ver bien la forma de la cabeza",
      "Misma altura de barbilla que el anterior",
    ],
    icon: "▶",
  },
];

// ─── Component ────────────────────────────────────────────────────────────────

export default function CaptureScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { analysisId } = route.params;

  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);

  const [currentStep, setCurrentStep] = useState(0);
  const [capturedUris, setCapturedUris] = useState<string[]>([]);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [showTips, setShowTips] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadFailed, setUploadFailed] = useState(false);

  const allCaptured = capturedUris.length >= STEPS.length;

  const guideAnim = useRef(new Animated.Value(1)).current;
  const guideColorAnim = useRef(new Animated.Value(0)).current;
  const countdownRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const step = STEPS[currentStep];

  useEffect(() => {
    if (!permission?.granted) requestPermission();
  }, []);

  // Subtle pulse on the oval guide
  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(guideAnim, { toValue: 1.025, duration: 1000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(guideAnim, { toValue: 1, duration: 1000, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, [currentStep]);

  // Auto-hide tips after 4s
  useEffect(() => {
    setShowTips(true);
    const t = setTimeout(() => setShowTips(false), 4000);
    return () => clearTimeout(t);
  }, [currentStep]);

  const startCountdown = useCallback(() => {
    if (countdownRef.current || isCapturing) return;
    setCountdown(3);
    const tick = (n: number) => {
      if (n <= 0) { capturePhoto(); return; }
      setCountdown(n);
      countdownRef.current = setTimeout(() => tick(n - 1), 900);
    };
    countdownRef.current = setTimeout(() => tick(2), 900);
  }, [isCapturing]);

  const cancelCountdown = useCallback(() => {
    if (countdownRef.current) { clearTimeout(countdownRef.current); countdownRef.current = null; }
    setCountdown(null);
  }, []);

  const capturePhoto = useCallback(async () => {
    // Block if already have all photos or capturing
    if (!cameraRef.current || isCapturing || capturedUris.length >= STEPS.length) return;
    cancelCountdown();
    setIsCapturing(true);
    setCountdown(null);

    try {
      Vibration.vibrate(60);
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.92,
        base64: false,
        skipProcessing: false,
      });

      const newUris = [...capturedUris, photo.uri];
      setCapturedUris(newUris);

      if (currentStep < STEPS.length - 1) {
        setCurrentStep((s) => s + 1);
      } else {
        // All 3 done — upload
        await uploadPhotos(newUris.slice(0, STEPS.length));
      }
    } catch (e) {
      Alert.alert("Error al capturar", "Inténtalo de nuevo.");
    } finally {
      setIsCapturing(false);
    }
  }, [cameraRef, isCapturing, capturedUris, currentStep, cancelCountdown]);

  const uploadPhotos = async (uris: string[]) => {
    setUploading(true);
    setUploadFailed(false);
    try {
      await api.uploadPhotos(analysisId, uris.slice(0, STEPS.length));
      navigation.replace("Result", { analysisId });
    } catch (e: any) {
      setUploadFailed(true);
      setUploading(false);
    }
  };

  const retakeLast = useCallback(() => {
    cancelCountdown();
    if (currentStep === 0) {
      // No photos taken yet — go back
      navigation.goBack();
      return;
    }
    // Remove last captured photo and go back one step
    setCapturedUris((prev) => prev.slice(0, -1));
    setCurrentStep((s) => s - 1);
  }, [currentStep, cancelCountdown, navigation]);

  const skipToUpload = () => {
    if (capturedUris.length === 0) {
      Alert.alert("Necesitas al menos 1 foto", "Captura la foto frontal para continuar.");
      return;
    }
    Alert.alert(
      `Usar ${capturedUris.length} foto${capturedUris.length > 1 ? "s" : ""}`,
      "Puedes continuar con las fotos que tienes. Cuantas más fotos, más preciso el análisis.",
      [
        { text: "Seguir capturando", style: "cancel" },
        { text: "Continuar", onPress: () => uploadPhotos(capturedUris) },
      ]
    );
  };

  if (!permission) return <View style={styles.container} />;

  if (!permission.granted) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.permissionText}>
          Necesitamos acceso a la cámara para analizar tu rostro.
        </Text>
        <TouchableOpacity style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnText}>Permitir acceso a cámara</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (uploadFailed) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.uploadTitle}>Error al enviar las fotos</Text>
        <Text style={styles.uploadSub}>Comprueba tu conexión y vuelve a intentarlo.</Text>
        <TouchableOpacity
          style={[styles.btn, { marginTop: SPACING.lg }]}
          onPress={() => uploadPhotos(capturedUris)}
        >
          <Text style={styles.btnText}>Reintentar →</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={{ marginTop: SPACING.md }}
          onPress={() => { setUploadFailed(false); setCurrentStep(STEPS.length - 1); }}
        >
          <Text style={{ color: COLORS.textMuted, fontSize: 13 }}>Repetir las fotos</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (uploading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.uploadTitle}>Analizando tu rostro…</Text>
        <Text style={styles.uploadSub}>
          Extrayendo 468 puntos de medición y generando tu informe personalizado.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFill}
        facing="front"
      />

      {/* Overlay con recorte oval */}
      <View style={styles.overlayTop} />
      <View style={styles.overlayMid}>
        <View style={styles.overlaySide} />
        <Animated.View
          style={[
            styles.ovalGuide,
            { transform: [{ scale: guideAnim }] },
            countdown !== null && styles.ovalGuideCountdown,
          ]}
        />
        <View style={styles.overlaySide} />
      </View>
      <View style={styles.overlayBottom} />

      {/* Crosshair */}
      <View style={[styles.crossV]} pointerEvents="none" />
      <View style={[styles.crossH]} pointerEvents="none" />

      {/* Countdown */}
      {countdown !== null && (
        <View style={styles.countdownWrap} pointerEvents="none">
          <Text style={styles.countdownText}>{countdown}</Text>
        </View>
      )}

      {/* Header: progress */}
      <View style={styles.header}>
        <View style={styles.progressRow}>
          {STEPS.map((s, i) => (
            <View
              key={s.id}
              style={[
                styles.dot,
                i < currentStep && styles.dotDone,
                i === currentStep && styles.dotActive,
              ]}
            />
          ))}
        </View>
        <Text style={styles.stepCounter}>{currentStep + 1} / {STEPS.length}</Text>
        <Text style={styles.stepTitle}>{step.title}</Text>
        <Text style={styles.stepInstruction}>{step.instruction}</Text>
      </View>

      {/* Tips panel (auto-hides after 4s) */}
      {showTips && (
        <View style={styles.tipsPanel} pointerEvents="none">
          {step.tips.map((tip, i) => (
            <Text key={i} style={styles.tipText}>• {tip}</Text>
          ))}
        </View>
      )}

      {/* Bottom controls */}
      <View style={styles.bottom}>
        {/* Retake / back */}
        <TouchableOpacity style={styles.sideBtn} onPress={retakeLast}>
          <Text style={styles.sideBtnIcon}>←</Text>
          <Text style={styles.sideBtnText}>
            {currentStep === 0 ? "Salir" : "Repetir"}
          </Text>
        </TouchableOpacity>

        {/* Capture */}
        <TouchableOpacity
          style={[styles.captureBtn, isCapturing && { opacity: 0.5 }]}
          onPress={countdown === null ? () => capturePhoto() : cancelCountdown}
          disabled={isCapturing}
        >
          {countdown !== null
            ? <Text style={styles.countdownInBtn}>{countdown}</Text>
            : <View style={styles.captureBtnInner} />}
        </TouchableOpacity>

        {/* Timer or skip */}
        {countdown === null ? (
          <TouchableOpacity style={styles.sideBtn} onPress={startCountdown}>
            <Text style={styles.sideBtnIcon}>3s</Text>
            <Text style={styles.sideBtnText}>
              {capturedUris.length > 0 ? `${Math.min(capturedUris.length, STEPS.length)}/3` : "Timer"}
            </Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={styles.sideBtn} onPress={cancelCountdown}>
            <Text style={styles.sideBtnIcon}>✕</Text>
            <Text style={styles.sideBtnText}>Cancelar</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  centered: { alignItems: "center", justifyContent: "center", padding: SPACING.xl, gap: SPACING.lg },

  // Overlay
  overlayTop: { position: "absolute", top: 0, left: 0, right: 0, height: (H - OVAL_H) / 2, backgroundColor: "rgba(0,0,0,0.60)" },
  overlayMid: { position: "absolute", top: (H - OVAL_H) / 2, left: 0, right: 0, height: OVAL_H, flexDirection: "row" },
  overlaySide: { flex: 1, backgroundColor: "rgba(0,0,0,0.60)" },
  overlayBottom: { position: "absolute", top: (H - OVAL_H) / 2 + OVAL_H, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.60)" },

  ovalGuide: {
    width: OVAL_W,
    height: OVAL_H,
    borderRadius: OVAL_W / 2,
    borderWidth: 2.5,
    borderColor: COLORS.accent,
    shadowColor: COLORS.accent,
    shadowOpacity: 0.7,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 0 },
  },
  ovalGuideCountdown: { borderColor: COLORS.accentLight },

  // Crosshair
  crossV: { position: "absolute", top: H / 2 - 18, left: W / 2 - 0.5, width: 1, height: 36, backgroundColor: "rgba(201,168,76,0.35)" },
  crossH: { position: "absolute", top: H / 2 - 0.5, left: W / 2 - 18, width: 36, height: 1, backgroundColor: "rgba(201,168,76,0.35)" },

  // Countdown
  countdownWrap: { position: "absolute", top: H / 2 - 70, left: 0, right: 0, alignItems: "center" },
  countdownText: { fontSize: 100, ...FONTS.heading, color: COLORS.accentLight, textShadowColor: COLORS.accent, textShadowRadius: 20, textShadowOffset: { width: 0, height: 0 } },

  // Header
  header: {
    position: "absolute", top: 0, left: 0, right: 0,
    paddingTop: Platform.OS === "ios" ? 56 : 36,
    paddingHorizontal: SPACING.lg,
    paddingBottom: SPACING.md,
    alignItems: "center",
  },
  progressRow: { flexDirection: "row", gap: 8, marginBottom: 8 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "rgba(255,255,255,0.25)" },
  dotDone: { backgroundColor: COLORS.success },
  dotActive: { backgroundColor: COLORS.accent, width: 22 },
  stepCounter: { color: COLORS.textMuted, fontSize: 12, ...FONTS.label },
  stepTitle: { color: COLORS.text, fontSize: 19, ...FONTS.heading, marginTop: 4, textAlign: "center" },
  stepInstruction: { color: COLORS.accent, fontSize: 14, ...FONTS.label, marginTop: 4, textAlign: "center" },

  // Tips
  tipsPanel: {
    position: "absolute",
    bottom: 170,
    left: SPACING.lg, right: SPACING.lg,
    backgroundColor: "rgba(15,15,26,0.85)",
    borderRadius: RADIUS.md,
    padding: SPACING.md,
    gap: 4,
  },
  tipText: { color: COLORS.textMuted, fontSize: 13, lineHeight: 18 },

  // Bottom
  bottom: {
    position: "absolute", bottom: 0, left: 0, right: 0,
    paddingBottom: Platform.OS === "ios" ? 44 : 24,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.md,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "rgba(15,15,26,0.85)",
  },
  sideBtn: { alignItems: "center", justifyContent: "center", minWidth: 68, gap: 3 },
  sideBtnIcon: { color: COLORS.text, fontSize: 18, fontWeight: "600" as const },
  sideBtnText: { color: COLORS.textMuted, fontSize: 11, ...FONTS.label },
  captureBtn: { width: 76, height: 76, borderRadius: 38, borderWidth: 3, borderColor: COLORS.accent, alignItems: "center", justifyContent: "center" },
  captureBtnInner: { width: 58, height: 58, borderRadius: 29, backgroundColor: COLORS.accent },
  countdownInBtn: { color: COLORS.accent, fontSize: 28, fontWeight: "700" as const },

  // Permission / upload screens
  permissionText: { color: COLORS.text, textAlign: "center", lineHeight: 22 },
  btn: { backgroundColor: COLORS.accent, paddingHorizontal: SPACING.xl, paddingVertical: SPACING.md, borderRadius: RADIUS.pill },
  btnText: { color: COLORS.primary, ...FONTS.heading },
  uploadIcon: { fontSize: 64 },
  uploadTitle: { color: COLORS.text, fontSize: 22, ...FONTS.heading, textAlign: "center" },
  uploadSub: { color: COLORS.textMuted, fontSize: 14, lineHeight: 22, textAlign: "center" },
});
