import type { ComponentProps } from "react";
import { cn } from "../lib/utils";

export function Input({ className, type = "text", ...props }: ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "w-full bg-transparent text-sm text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)] disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
