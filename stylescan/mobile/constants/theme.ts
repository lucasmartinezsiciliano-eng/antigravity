export const COLORS = {
  // Brand
  primary: "#1A1A2E",      // Deep navy — professional, masculine
  accent: "#C9A84C",       // Gold — premium feel
  accentLight: "#F0D080",

  // UI
  bg: "#0F0F1A",
  surface: "#1E1E30",
  border: "#2A2A40",
  text: "#F0F0F0",
  textMuted: "#8888AA",

  // Status
  success: "#4CAF7C",
  warning: "#F0A830",
  error: "#E05555",

  // Capture screen
  captureOverlay: "rgba(0,0,0,0.55)",
  captureGuide: "#C9A84C",
  captureGuideGlow: "rgba(201,168,76,0.35)",
  captureSuccess: "#4CAF7C",
};

export const FONTS = {
  heading: { fontWeight: "700" as const, letterSpacing: -0.5 },
  body: { fontWeight: "400" as const, lineHeight: 22 },
  label: { fontWeight: "600" as const, letterSpacing: 0.3 },
  mono: { fontFamily: "monospace" },
};

export const SPACING = {
  xs: 4, sm: 8, md: 16, lg: 24, xl: 40,
};

export const RADIUS = {
  sm: 8, md: 14, lg: 22, pill: 999,
};
