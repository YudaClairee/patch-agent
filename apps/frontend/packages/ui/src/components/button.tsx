import type { ComponentProps, ReactNode } from "react";
import { patchClasses } from "../classes";
import { cn } from "../lib/utils";

type ButtonVariant = "primary" | "secondary" | "chip" | "danger";

type ButtonProps = ComponentProps<"button"> & {
  children: ReactNode;
  variant?: ButtonVariant;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "border border-[var(--patch-accent)] bg-[var(--patch-accent)] text-white hover:bg-[var(--patch-accent-hover)] focus-visible:outline-[var(--patch-accent)]",
  secondary:
    "border border-[var(--patch-border-strong)] bg-[var(--patch-surface)] text-[var(--patch-ink)] hover:bg-[var(--patch-bg)] focus-visible:outline-[var(--patch-ink)]",
  chip: "bg-[var(--patch-chip)] text-[var(--patch-ink)] backdrop-blur-[20px] hover:bg-[var(--patch-chip-hover)] focus-visible:outline-[var(--patch-ink)]",
  danger:
    "border border-[var(--patch-border-strong)] bg-[var(--patch-surface)] text-[var(--patch-ink)] hover:bg-[var(--patch-bg)] focus-visible:outline-[var(--patch-ink)]",
};

export function Button({ children, variant = "primary", className, type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-full text-sm font-medium tracking-[-0.003em] transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:opacity-50",
        patchClasses.shape.control,
        variants[variant],
        "min-h-9 px-4 py-2",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
