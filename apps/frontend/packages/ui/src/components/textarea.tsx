import type { ComponentProps } from "react";
import { cn } from "../lib/utils";

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "resize-none bg-transparent text-base leading-6 text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)] disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
