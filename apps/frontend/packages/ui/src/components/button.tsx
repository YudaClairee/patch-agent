import type { ComponentProps, ReactNode } from "react";
import { cn } from "../lib/utils";

type ButtonProps = ComponentProps<"button"> & {
  children: ReactNode;
};

export function Button({ children, className, type = "button", ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 border border-[var(--patch-border-strong)] bg-transparent px-3 py-1 text-sm text-[var(--patch-fg)] transition hover:border-[var(--patch-fg)] hover:text-[var(--patch-accent)] focus-visible:outline focus-visible:outline-1 focus-visible:outline-[var(--patch-accent)] disabled:cursor-not-allowed disabled:opacity-40",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
