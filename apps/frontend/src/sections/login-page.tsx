import { cn, patchClasses } from "@patch/ui";
import { useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion, useMotionValue, useTransform } from "framer-motion";
import { ArrowRight, CheckCircle2, Eye, EyeOff, GitBranch, KeyRound, Loader2, Mail, ShieldCheck } from "lucide-react";
import { type FormEvent, memo, type PointerEvent, type ReactNode, useState } from "react";
import { patchApi } from "../api-contract";

type LoginState = "idle" | "loading" | "success" | "error";

const signInOptions = ["GitHub", "GitLab", "SSO"] as const;

const workspaceSignals = [
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

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("hendra@patch.dev");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberWorkspace, setRememberWorkspace] = useState(true);
  const [loginState, setLoginState] = useState<LoginState>("idle");

  const errorMessage =
    loginState === "error" ? "Masukkan email yang valid dan password minimal 8 karakter." : undefined;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!email.includes("@") || password.length < 8) {
      setLoginState("error");
      return;
    }

    setLoginState("loading");

    try {
      await patchApi.login({ email, password });
      setLoginState("success");
      void navigate({ to: "/dashboard" });
    } catch {
      setLoginState("error");
    }
  };

  return (
    <main
      className={cn(
        "min-h-[100dvh] overflow-hidden bg-[var(--patch-bg)] text-[var(--patch-ink)] [font-family:var(--patch-font-sans)]",
        patchClasses.appSurface,
      )}
    >
      <div className="mx-auto grid min-h-[900px] w-full max-w-[1400px] grid-cols-1 px-4 py-4 md:px-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:px-8 lg:py-8">
        <section
          aria-labelledby="login-title"
          className="relative flex min-h-[calc(100dvh-2rem)] items-center border border-[var(--patch-border)] bg-[var(--patch-surface)] px-4 py-8 sm:px-8 lg:min-h-[calc(100dvh-4rem)] lg:rounded-l-[36px] lg:border-r-0 lg:px-12 xl:px-16"
        >
          <div className="w-full max-w-[560px]">
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 110, damping: 22 }}
            >
              <div className="hidden w-fit shrink-0 items-center gap-2 rounded-full bg-[var(--patch-chip)] px-3.5 py-2 text-sm font-medium text-[var(--patch-ink)] backdrop-blur-[20px] md:inline-flex">
                <ShieldCheck size={16} />
                Protected workspace
              </div>
              <h1 id="login-title" className="sr-only">
                Masuk ke workspace P.A.T.C.H.
              </h1>
              <img
                src="/patch.svg"
                alt="P.A.T.C.H."
                className="h-auto w-full max-w-[420px] object-contain md:max-w-[500px]"
              />
              <p className="max-w-[48ch] text-base leading-7 text-[var(--patch-text)] md:text-lg">
                Turns natural-language coding tasks into reviewable GitHub pull requests.
              </p>
            </motion.div>

            <motion.form
              onSubmit={handleSubmit}
              className="mt-10 rounded-[28px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-5 shadow-[0_20px_44px_-24px_rgba(29,29,31,0.2)] md:p-6"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.08 }}
            >
              <div className="grid gap-4">
                <FormField
                  id="email"
                  label="Email"
                  helper="Gunakan email workspace yang terhubung dengan repository."
                  error={loginState === "error" ? "Email belum valid." : undefined}
                  className="bg-[var(--patch-surface)]"
                >
                  <Mail size={17} className="text-[var(--patch-muted)]" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={email}
                    onChange={(event) => {
                      setEmail(event.target.value);
                      if (loginState === "error") {
                        setLoginState("idle");
                      }
                    }}
                    autoComplete="email"
                    className="min-w-0 flex-1 bg-transparent text-sm text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
                    placeholder="name@company.dev"
                  />
                </FormField>

                <FormField
                  id="password"
                  label="Password"
                  helper="Minimal 8 karakter. Secret tidak disimpan di browser."
                  error={loginState === "error" ? "Password terlalu pendek." : undefined}
                  className="bg-[var(--patch-surface)]"
                >
                  <KeyRound size={17} className="text-[var(--patch-muted)]" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(event) => {
                      setPassword(event.target.value);
                      if (loginState === "error") {
                        setLoginState("idle");
                      }
                    }}
                    autoComplete="current-password"
                    className="min-w-0 flex-1 bg-transparent text-sm text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
                    placeholder="Workspace password"
                  />
                  <button
                    type="button"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    onClick={() => setShowPassword((current) => !current)}
                    className="flex h-8 w-8 items-center justify-center rounded-full text-[var(--patch-muted)] transition hover:bg-[var(--patch-border)] hover:text-[var(--patch-ink)] active:scale-[0.98]"
                  >
                    {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </FormField>
              </div>

              <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <label className="flex items-center gap-2 text-sm text-[var(--patch-text)]">
                  <input
                    type="checkbox"
                    checked={rememberWorkspace}
                    onChange={(event) => setRememberWorkspace(event.target.checked)}
                    className="h-4 w-4 accent-[var(--patch-accent)]"
                  />
                  Keep this workspace on this device
                </label>
                <a
                  href="/"
                  className="text-sm font-medium text-[var(--patch-ink)] underline decoration-[var(--patch-border-strong)] underline-offset-4"
                >
                  Reset access
                </a>
              </div>

              <AnimatePresence mode="wait">
                {errorMessage && (
                  <motion.p
                    key="error"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="mt-5 rounded-[18px] border border-[var(--patch-border-strong)] bg-[var(--patch-surface)] px-4 py-3 text-sm text-[var(--patch-ink)]"
                  >
                    {errorMessage}
                  </motion.p>
                )}
              </AnimatePresence>

              <MagneticSubmitButton state={loginState} />

              <div className="mt-5 grid grid-cols-3 gap-2">
                {signInOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className="flex min-h-10 items-center justify-center gap-2 rounded-full border border-[var(--patch-border)] bg-[var(--patch-surface)] px-3 text-sm font-medium text-[var(--patch-ink)] transition hover:bg-[var(--patch-border)] active:scale-[0.98]"
                  >
                    {option === "GitHub" && <GitBranch size={16} />}
                    {option}
                  </button>
                ))}
              </div>
            </motion.form>
          </div>
        </section>
        <LoginWorkspacePreview state={loginState} rememberWorkspace={rememberWorkspace} />
      </div>
    </main>
  );
}

type FormFieldProps = {
  id: string;
  label: string;
  helper: string;
  error?: string;
  className?: string;
  children: ReactNode;
};

function FormField({ id, label, helper, error, className, children }: FormFieldProps) {
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

type MagneticSubmitButtonProps = {
  state: LoginState;
};

function MagneticSubmitButton({ state }: MagneticSubmitButtonProps) {
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
      className="mt-6 flex min-h-12 w-full items-center justify-center gap-2 rounded-full bg-[var(--patch-accent)] px-5 text-sm font-semibold text-white transition hover:bg-[var(--patch-accent-hover)] disabled:pointer-events-none disabled:opacity-90"
    >
      {state === "loading" && <Loader2 size={17} className="animate-spin" />}
      {state === "success" && <CheckCircle2 size={17} />}
      {state === "idle" || state === "error" ? (
        <>
          Sign in
          <ArrowRight size={17} />
        </>
      ) : null}
      {state === "loading" && "Verifying workspace"}
      {state === "success" && "Workspace ready"}
    </motion.button>
  );
}

type LoginWorkspacePreviewProps = {
  state: LoginState;
  rememberWorkspace: boolean;
};

const LoginWorkspacePreview = memo(function LoginWorkspacePreview({
  state,
  rememberWorkspace,
}: LoginWorkspacePreviewProps) {
  const previewState = state === "success" ? "restored" : state === "loading" ? "verifying" : "no active session";

  return (
    <section
      aria-label="Workspace preview"
      className="relative flex min-h-[calc(100dvh-2rem)] items-center overflow-hidden border-x border-b border-[var(--patch-border)] bg-[var(--patch-ink)] px-4 py-8 text-white sm:px-8 lg:min-h-[calc(100dvh-4rem)] lg:rounded-r-[36px] lg:border lg:px-10 xl:px-14"
    >
      <motion.div
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 90, damping: 20, delay: 0.14 }}
        className="relative mx-auto w-full max-w-[520px] lg:ml-auto"
      >
        {/* <div className="absolute left-[-14%] top-[-8%] h-40 w-40 rounded-[48px] bg-white opacity-[0.08]" /> */}
        {/* <div className="absolute bottom-[-10%] right-[-12%] h-52 w-52 rounded-[56px] border border-white/10" /> */}
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
            {workspaceSignals.map((item, index) => (
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
                <p className="text-sm text-[var(--patch-on-dark-muted)]">Latest run</p>
                <p className="mt-2 text-xl font-semibold leading-tight">pytest gate before PR</p>
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
