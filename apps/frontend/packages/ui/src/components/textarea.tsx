import type { ComponentProps } from "react";
import { cn } from "../lib/utils";

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "w-full resize-y border border-[var(--patch-border)] bg-[var(--patch-surface)] px-2 py-1 text-sm leading-5 text-[var(--patch-fg)] outline-none placeholder:text-[var(--patch-dim)] focus:border-[var(--patch-accent)] disabled:opacity-40",
        className,
      )}
      {...props}
    />
  );
}
