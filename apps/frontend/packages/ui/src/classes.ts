export const patchClasses = {
  appSurface: "bg-[var(--patch-bg)] text-[var(--patch-ink)] [font-family:var(--patch-font-sans)]",
  border: {
    subtle: "border-[var(--patch-border)]",
    strong: "border-[var(--patch-border-strong)]",
    dark: "border-[var(--patch-dark-border)]",
  },
  surface: {
    page: "bg-[var(--patch-bg)]",
    panel: "bg-[var(--patch-surface)]",
    panelTranslucent: "bg-[var(--patch-surface-translucent)]",
    elevated: "border border-[var(--patch-border)] bg-[var(--patch-surface)]",
    subtle: "border border-[var(--patch-border)] bg-[var(--patch-bg)]",
    dark: "bg-[var(--patch-ink)] text-white",
    onDark: "border border-[var(--patch-on-dark-panel)] bg-[var(--patch-on-dark-panel)] text-white",
  },
  text: {
    ink: "text-[var(--patch-ink)]",
    body: "text-[var(--patch-text)]",
    muted: "text-[var(--patch-muted)]",
    onDarkMuted: "text-[var(--patch-on-dark-muted)]",
  },
  shape: {
    control: "rounded-full",
    card: "rounded-[28px]",
    panel: "rounded-[24px]",
    tile: "rounded-[18px]",
    input: "rounded-[16px]",
  },
  focus: {
    ink: "focus-visible:outline-[var(--patch-ink)]",
    accent: "focus-visible:outline-[var(--patch-accent)]",
  },
  iconTile:
    "flex h-11 w-11 shrink-0 items-center justify-center rounded-[16px] border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-ink)]",
  tracking: {
    tight: "tracking-[-0.003em]",
    tighter: "tracking-[-0.006em]",
    display: "tracking-[-0.36px]",
    metric: "tracking-[-0.6px]",
  },
} as const;
