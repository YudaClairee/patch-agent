import { FileCode2 } from "lucide-react";
import { type ComponentProps, type ReactNode, useId } from "react";
import { patchClasses } from "../classes";
import { cn } from "../lib/utils";
import { Input } from "./input";

type SectionHeadingProps = {
  title: string;
  action?: ReactNode;
};

export function SectionHeading({ title, action }: SectionHeadingProps) {
  return (
    <div className="flex items-center justify-between gap-3">
      <h2 className={cn("text-xl font-semibold leading-tight", patchClasses.tracking.display, patchClasses.text.ink)}>
        {title}
      </h2>
      {action}
    </div>
  );
}

type StatusLineProps = {
  label: string;
  value: string;
  tone?: "light" | "dark";
};

export function StatusLine({ label, value, tone = "light" }: StatusLineProps) {
  const styles =
    tone === "dark"
      ? patchClasses.surface.onDark
      : "border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-ink)]";

  return (
    <div
      className={cn("grid min-h-16 min-w-0 content-start gap-1.5 rounded-[18px] px-3 py-3 text-sm leading-5", styles)}
    >
      <span className="min-w-0 text-inherit opacity-70">{label}</span>
      <span className="min-w-0 font-semibold text-inherit [overflow-wrap:anywhere]">{value}</span>
    </div>
  );
}

type FieldProps = Omit<ComponentProps<typeof Input>, "id" | "placeholder"> & {
  label: string;
  placeholder: string;
  icon?: ReactNode;
  secure?: boolean;
};

export function Field({ label, placeholder, icon, secure = false, type = "text", ...inputProps }: FieldProps) {
  const fieldId = useId();

  return (
    <label className="block" htmlFor={fieldId}>
      <div className={cn("mb-2 text-sm font-semibold", patchClasses.tracking.tight, patchClasses.text.ink)}>
        {label}
      </div>
      <div className="flex min-h-11 items-center gap-2 rounded-[16px] border border-[var(--patch-border)] bg-[var(--patch-bg)] px-3 transition focus-within:border-[var(--patch-ink)]">
        {icon && <span className={patchClasses.text.body}>{icon}</span>}
        <Input id={fieldId} type={secure ? "password" : type} placeholder={placeholder} {...inputProps} />
      </div>
    </label>
  );
}

type FileRowProps = {
  path: string;
  additions: string;
  deletions: string;
};

export function FileRow({ path, additions, deletions }: FileRowProps) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-3">
      <div className="flex min-w-0 items-center gap-2">
        <FileCode2 size={16} className={cn("shrink-0", patchClasses.text.body)} />
        <span className={cn("truncate font-medium", patchClasses.text.ink)}>{path}</span>
      </div>
      <div className={cn("flex shrink-0 gap-2 text-xs font-semibold", patchClasses.text.ink)}>
        <span>{additions}</span>
        <span>{deletions}</span>
      </div>
    </div>
  );
}
