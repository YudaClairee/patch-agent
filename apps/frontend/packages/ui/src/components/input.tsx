import type { ComponentProps } from "react";
import { cn } from "../lib/utils";

export function Input({ className, type = "text", ...props }: ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "w-full border border-[var(--patch-border)] bg-[var(--patch-surface)] px-2 py-1 text-sm text-[var(--patch-fg)] outline-none placeholder:text-[var(--patch-dim)] focus:border-[var(--patch-accent)] disabled:opacity-40",
        className,
      )}
      {...props}
    />
  );
}
