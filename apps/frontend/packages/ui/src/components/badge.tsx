import type { ComponentProps, ReactNode } from "react";
import { cn } from "../lib/utils";

type BadgeTone = "default" | "inverse";

type BadgeProps = ComponentProps<"span"> & {
  children: ReactNode;
  tone?: BadgeTone;
};

const tones: Record<BadgeTone, string> = {
  default: "border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-ink)]",
  inverse: "bg-[var(--patch-ink)] text-white",
};

export function Badge({ children, tone = "default", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex h-7 items-center rounded-full px-3 text-xs font-semibold tracking-[-0.003em]",
        tones[tone],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
