import type { ComponentProps, ReactNode } from "react";
import { patchClasses } from "../classes";
import { cn } from "../lib/utils";

type CardSurface = "white" | "dark";

type CardProps = ComponentProps<"section"> & {
  children: ReactNode;
  surface?: CardSurface;
};

const surfaces: Record<CardSurface, string> = {
  white: "border-[var(--patch-border)] bg-[var(--patch-surface)] text-[var(--patch-ink)]",
  dark: "border-[var(--patch-ink)] bg-[var(--patch-ink)] text-white",
};

export function Card({ children, surface = "white", className, ...props }: CardProps) {
  return (
    <section className={cn(patchClasses.shape.card, "border", surfaces[surface], className)} {...props}>
      {children}
    </section>
  );
}
