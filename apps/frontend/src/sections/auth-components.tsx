import { cn } from "@patch/ui";
import { motion, useMotionValue, useTransform } from "framer-motion";
import { ArrowRight, CheckCircle2, Loader2, ShieldCheck } from "lucide-react";
import { memo, type PointerEvent, type ReactNode } from "react";

export type AuthFlowState = "idle" | "loading" | "success" | "error";

type AuthSignal = {
  label: string;
  value: string;
};

const defaultWorkspaceSignals = [
  { label: "Repository access", value: "3 scopes" },
  { label: "Secret policy", value: "redacted" },
  { label: "PR handoff", value: "enabled" },
] as const;

const previewTickerItems = [
  { id: "repo-indexed-a", label: "repo indexed" },
  { id: "tests-gated-a", label: "tests gated" },
  { id: "token-redacted-a", label: "token redacted" },
  { id: "pr-queued-a", label: "PR queued" },
  { id: "repo-indexed-b", label: "repo indexed" },
  { id: "tests-gated-b", label: "tests gated" },
  { id: "token-redacted-b", label: "token redacted" },
  { id: "pr-queued-b", label: "PR queued" },
] as const;

type FormFieldProps = {
  id: string;
  label: string;
  helper: string;
  error?: string;
  className?: string;
  children: ReactNode;
};

export function FormField({ id, label, helper, error, className, children }: FormFieldProps) {
  return (
    <div className="grid gap-2">
      <label htmlFor={id} className="text-sm font-semibold text-[var(--patch-ink)]">
        {label}
      </label>
      <div
        className={cn(
          "flex min-h-12 items-center gap-3 rounded-[18px] border bg-white px-3.5 transition focus-within:border-[var(--patch-ink)]",
          error ? "border-[var(--patch-border-strong)]" : "border-[var(--patch-border)]",
          className,
        )}
      >
        {children}
      </div>
      <p className={`text-xs leading-5 ${error ? "text-[var(--patch-ink)]" : "text-[var(--patch-muted)]"}`}>
        {error ?? helper}
      </p>
    </div>
  );
}

type AuthSubmitButtonProps = {
  state: AuthFlowState;
  idleLabel: string;
  loadingLabel: string;
  successLabel: string;
  className?: string;
};

export function AuthSubmitButton({ state, idleLabel, loadingLabel, successLabel, className }: AuthSubmitButtonProps) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const transformX = useTransform(x, [-90, 90], [-5, 5]);
  const transformY = useTransform(y, [-40, 40], [-3, 3]);
  const isBusy = state === "loading" || state === "success";

  const handlePointerMove = (event: PointerEvent<HTMLButtonElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    x.set(event.clientX - rect.left - rect.width / 2);
    y.set(event.clientY - rect.top - rect.height / 2);
  };

  const resetPointer = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.button
      type="submit"
      disabled={isBusy}
      onPointerMove={handlePointerMove}
      onPointerLeave={resetPointer}
      style={{ x: transformX, y: transformY }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 120, damping: 18 }}
      className={cn(
        "mt-6 flex min-h-12 w-full items-center justify-center gap-2 rounded-full bg-[var(--patch-accent)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--patch-accent-hover)] disabled:pointer-events-none disabled:opacity-90",
        className,
      )}
    >
      {state === "loading" && <Loader2 size={17} className="animate-spin" />}
      {state === "success" && <CheckCircle2 size={17} />}
      {state === "idle" || state === "error" ? (
        <>
          {idleLabel}
          <ArrowRight size={17} />
        </>
      ) : null}
      {state === "loading" && loadingLabel}
      {state === "success" && successLabel}
    </motion.button>
  );
}

type AuthWorkspacePreviewProps = {
  state: AuthFlowState;
  rememberWorkspace?: boolean;
  ariaLabel?: string;
  idleStateLabel?: string;
  loadingStateLabel?: string;
  successStateLabel?: string;
  latestRunLabel?: string;
  latestRunTitle?: string;
  signals?: readonly AuthSignal[];
};

export const AuthWorkspacePreview = memo(function AuthWorkspacePreview({
  state,
  rememberWorkspace = true,
  ariaLabel = "Workspace preview",
  idleStateLabel = "no active session",
  loadingStateLabel = "verifying",
  successStateLabel = "restored",
  latestRunLabel = "Latest run",
  latestRunTitle = "pytest gate before PR",
  signals = defaultWorkspaceSignals,
}: AuthWorkspacePreviewProps) {
  const previewState =
    state === "success" ? successStateLabel : state === "loading" ? loadingStateLabel : idleStateLabel;

  return (
    <section
      aria-label={ariaLabel}
      className="relative flex min-h-[calc(100dvh-2rem)] items-center overflow-hidden border-x border-b border-[var(--patch-border)] bg-[var(--patch-ink)] px-4 py-8 text-white sm:px-8 lg:min-h-[calc(100dvh-4rem)] lg:rounded-r-[36px] lg:border lg:px-10 xl:px-14"
    >
      <motion.div
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 90, damping: 20, delay: 0.14 }}
        className="relative mx-auto w-full max-w-[520px] lg:ml-auto"
      >
        <div className="relative rounded-[36px] border border-white/10 bg-[var(--patch-surface)] p-5 text-[var(--patch-ink)] shadow-[inset_0_1px_0_rgba(255,255,255,0.28),0_28px_72px_-34px_rgba(0,0,0,0.68)] sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-[var(--patch-muted)]">Session state</p>
              <h2 className="mt-2 text-[34px] font-bold leading-none text-[var(--patch-ink)] sm:text-[40px]">
                {previewState}
              </h2>
            </div>
            <motion.span
              animate={{ scale: [1, 1.18, 1], opacity: [0.72, 1, 0.72] }}
              transition={{ duration: 2.2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
              className="mt-1 h-3 w-3 rounded-full bg-[var(--patch-accent)]"
            />
          </div>

          <div className="mt-8 grid gap-3">
            {signals.map((item, index) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.2 + index * 0.08 }}
                className="grid grid-cols-[1fr_auto] items-center gap-4 rounded-[22px] bg-[var(--patch-bg)] px-4 py-3"
              >
                <span className="text-sm text-[var(--patch-muted)]">{item.label}</span>
                <span className="font-mono text-sm font-semibold text-[var(--patch-ink)]">{item.value}</span>
              </motion.div>
            ))}
          </div>

          <div className="mt-8 rounded-[28px] bg-[var(--patch-ink)] p-5 text-white">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm text-[var(--patch-on-dark-muted)]">{latestRunLabel}</p>
                <p className="mt-2 text-xl font-semibold leading-tight">{latestRunTitle}</p>
              </div>
              <ShieldCheck size={22} />
            </div>
            <div className="mt-5 grid gap-2">
              <PreviewMeter label="Context" value="84%" width="w-[84%]" />
              <PreviewMeter label="Verification" value="47.2%" width="w-[47.2%]" />
              <PreviewMeter
                label="Device trust"
                value={rememberWorkspace ? "on" : "off"}
                width={rememberWorkspace ? "w-[68%]" : "w-[24%]"}
              />
            </div>
          </div>

          <div className="mt-5 overflow-hidden rounded-[28px] border border-[var(--patch-border)] bg-[var(--patch-bg)]">
            <motion.div
              animate={{ x: ["0%", "-50%"] }}
              transition={{ duration: 18, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
              className="flex w-max gap-2 px-3 py-3"
            >
              {previewTickerItems.map((item) => (
                <span
                  key={item.id}
                  className="rounded-full bg-[var(--patch-surface)] px-3 py-1.5 text-xs font-semibold text-[var(--patch-ink)]"
                >
                  {item.label}
                </span>
              ))}
            </motion.div>
          </div>
        </div>
      </motion.div>
    </section>
  );
});

type PreviewMeterProps = {
  label: string;
  value: string;
  width: string;
};

function PreviewMeter({ label, value, width }: PreviewMeterProps) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-[var(--patch-on-dark-muted)]">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[var(--patch-on-dark-panel)]">
        <motion.div
          initial={{ opacity: 0.65, scaleX: 0.78 }}
          animate={{ opacity: [0.65, 1, 0.65], scaleX: [0.78, 1, 0.78] }}
          transition={{ duration: 2.4, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
          className={`h-full origin-left rounded-full bg-white ${width}`}
        />
      </div>
    </div>
  );
}
