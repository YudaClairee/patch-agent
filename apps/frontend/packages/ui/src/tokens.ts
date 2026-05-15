export const patchColors = {
  bg: "#0b0b0b",
  surface: "#111111",
  border: "#2a2a2a",
  borderStrong: "#3a3a3a",
  fg: "#e6e6e6",
  dim: "#888888",
  accent: "#4ade80",
  warn: "#facc15",
  error: "#f87171",
} as const;

export const patchCssVars = {
  bg: "var(--patch-bg)",
  surface: "var(--patch-surface)",
  border: "var(--patch-border)",
  borderStrong: "var(--patch-border-strong)",
  fg: "var(--patch-fg)",
  dim: "var(--patch-dim)",
  accent: "var(--patch-accent)",
  warn: "var(--patch-warn)",
  error: "var(--patch-error)",
} as const;
