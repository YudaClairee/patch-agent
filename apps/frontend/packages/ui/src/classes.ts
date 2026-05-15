export const patchClasses = {
  app: "bg-[var(--patch-bg)] text-[var(--patch-fg)] font-mono",
  border: "border border-[var(--patch-border)]",
  borderStrong: "border border-[var(--patch-border-strong)]",
  text: {
    fg: "text-[var(--patch-fg)]",
    dim: "text-[var(--patch-dim)]",
    accent: "text-[var(--patch-accent)]",
    warn: "text-[var(--patch-warn)]",
    error: "text-[var(--patch-error)]",
  },
  surface: {
    bg: "bg-[var(--patch-bg)]",
    panel: "bg-[var(--patch-surface)]",
  },
} as const;
