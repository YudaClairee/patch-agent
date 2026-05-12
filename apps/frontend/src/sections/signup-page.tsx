import { cn, patchClasses } from "@patch/ui";
import { Link, useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import {
  CheckCircle2,
  Code2,
  Eye,
  EyeOff,
  GitBranch,
  KeyRound,
  LockKeyhole,
  type LucideIcon,
  Mail,
  ServerCog,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { type FormEvent, memo, useState } from "react";
import { patchApi } from "../api-contract";
import { type AuthFlowState, AuthSubmitButton, FormField } from "./auth-components";

type SignupField = "name" | "email" | "password" | "confirmPassword";
type SignupFieldErrors = Partial<Record<SignupField, string>>;

const signupPreviewSteps: Array<{ id: string; label: string; value: string; icon: LucideIcon }> = [
  { id: "account", label: "Account", value: "identity sealed", icon: UserRound },
  { id: "session", label: "Session", value: "httpOnly cookie", icon: LockKeyhole },
  { id: "repo", label: "Repository", value: "connect next", icon: GitBranch },
  { id: "agent", label: "Agent", value: "PR path ready", icon: ServerCog },
];

const signupPreviewCards = [
  { id: "profile", label: "Profile", value: "workspace owner", width: "w-[72%]" },
  { id: "quota", label: "Daily runs", value: "calibrated", width: "w-[58%]" },
  { id: "handoff", label: "Review flow", value: "waiting", width: "w-[84%]" },
] as const;

const formContainerVariants: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 20,
      delay: 0.08,
      staggerChildren: 0.045,
    },
  },
};

const formItemVariants: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 20 } },
};

function isValidEmail(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export function SignUpPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [signupState, setSignupState] = useState<AuthFlowState>("idle");
  const [fieldErrors, setFieldErrors] = useState<SignupFieldErrors>({});
  const [submitError, setSubmitError] = useState<string | undefined>();

  const clearFieldError = (field: SignupField) => {
    setFieldErrors((current) => {
      if (!current[field]) {
        return current;
      }

      const next = { ...current };
      delete next[field];
      return next;
    });
    setSubmitError(undefined);
    if (signupState === "error") {
      setSignupState("idle");
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedEmail = email.trim().toLowerCase();
    const trimmedName = name.trim();
    const nextErrors: SignupFieldErrors = {};

    if (name && trimmedName.length < 2) {
      nextErrors.name = "Nama terlalu pendek.";
    }

    if (!isValidEmail(normalizedEmail)) {
      nextErrors.email = "Email workspace belum valid.";
    }

    if (password.length < 8) {
      nextErrors.password = "Password minimal 8 karakter.";
    }

    if (confirmPassword !== password) {
      nextErrors.confirmPassword = "Konfirmasi password belum sama.";
    }

    if (Object.keys(nextErrors).length > 0) {
      setFieldErrors(nextErrors);
      setSubmitError("Periksa kembali detail akun sebelum membuat workspace.");
      setSignupState("error");
      return;
    }

    setFieldErrors({});
    setSubmitError(undefined);
    setSignupState("loading");

    try {
      await patchApi.signup({
        email: normalizedEmail,
        password,
        name: trimmedName || null,
      });
      setSignupState("success");
      void navigate({ to: "/dashboard" });
    } catch (error) {
      setSignupState("error");
      setSubmitError(error instanceof Error ? error.message : "Account creation failed. Please try again.");
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
          aria-labelledby="signup-title"
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
                Account setup
              </div>
              <h1 id="signup-title" className="sr-only">
                Buat akun P.A.T.C.H.
              </h1>
              <img
                src="/patch.svg"
                alt="P.A.T.C.H."
                className="h-auto w-full max-w-[420px] object-contain md:max-w-[500px]"
              />
              <p className="max-w-[48ch] text-base leading-7 text-[var(--patch-text)] md:text-lg">
                Create a secure workspace before connecting repositories and shipping reviewable pull requests.
              </p>
            </motion.div>

            <motion.form
              onSubmit={handleSubmit}
              className="mt-8 rounded-[28px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-5 shadow-[0_20px_44px_-24px_rgba(29,29,31,0.2)] md:p-6"
              variants={formContainerVariants}
              initial="hidden"
              animate="visible"
            >
              <motion.div className="grid gap-4" variants={formContainerVariants}>
                <motion.div variants={formItemVariants}>
                  <FormField
                    id="signup-name"
                    label="Name"
                    helper="Optional. Used for workspace ownership and handoff labels."
                    error={fieldErrors.name}
                    className="bg-[var(--patch-surface)]"
                  >
                    <UserRound size={17} className="text-[var(--patch-muted)]" />
                    <input
                      id="signup-name"
                      name="name"
                      type="text"
                      value={name}
                      onChange={(event) => {
                        setName(event.target.value);
                        clearFieldError("name");
                      }}
                      autoComplete="name"
                      className="min-w-0 flex-1 bg-transparent text-sm text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
                      placeholder="Hendra Pratama"
                    />
                  </FormField>
                </motion.div>

                <motion.div variants={formItemVariants}>
                  <FormField
                    id="signup-email"
                    label="Email"
                    helper="This email is sent to POST /auth/signup and becomes your user profile email."
                    error={fieldErrors.email}
                    className="bg-[var(--patch-surface)]"
                  >
                    <Mail size={17} className="text-[var(--patch-muted)]" />
                    <input
                      id="signup-email"
                      name="email"
                      type="email"
                      value={email}
                      onChange={(event) => {
                        setEmail(event.target.value);
                        clearFieldError("email");
                      }}
                      autoComplete="email"
                      className="min-w-0 flex-1 bg-transparent text-sm text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
                      placeholder="name@company.dev"
                    />
                  </FormField>
                </motion.div>

                <motion.div variants={formItemVariants}>
                  <FormField
                    id="signup-password"
                    label="Password"
                    helper="Minimal 8 karakter. Stream 1 akan membuat cookie auth httpOnly setelah signup."
                    error={fieldErrors.password}
                    className="bg-[var(--patch-surface)]"
                  >
                    <KeyRound size={17} className="text-[var(--patch-muted)]" />
                    <input
                      id="signup-password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(event) => {
                        setPassword(event.target.value);
                        clearFieldError("password");
                      }}
                      autoComplete="new-password"
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
                </motion.div>

                <motion.div variants={formItemVariants}>
                  <FormField
                    id="signup-confirm-password"
                    label="Confirm password"
                    helper="Repeat the same password before the account creation request is sent."
                    error={fieldErrors.confirmPassword}
                    className="bg-[var(--patch-surface)]"
                  >
                    <KeyRound size={17} className="text-[var(--patch-muted)]" />
                    <input
                      id="signup-confirm-password"
                      name="confirmPassword"
                      type={showPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(event) => {
                        setConfirmPassword(event.target.value);
                        clearFieldError("confirmPassword");
                      }}
                      autoComplete="new-password"
                      className="min-w-0 flex-1 bg-transparent text-sm text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
                      placeholder="Repeat password"
                    />
                  </FormField>
                </motion.div>
              </motion.div>

              <AnimatePresence mode="wait">
                {submitError && (
                  <motion.p
                    key="signup-error"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    className="mt-5 rounded-[18px] border border-[var(--patch-border-strong)] bg-[var(--patch-surface)] px-4 py-3 text-sm text-[var(--patch-ink)]"
                  >
                    {submitError}
                  </motion.p>
                )}
              </AnimatePresence>

              <AuthSubmitButton
                state={signupState}
                idleLabel="Create account"
                loadingLabel="Creating account"
                successLabel="Workspace created"
              />

              <div className="mt-5 flex flex-col gap-3 border-t border-[var(--patch-border)] pt-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-[var(--patch-ink)]">Already have access?</p>
                  <p className="mt-1 text-xs leading-5 text-[var(--patch-muted)]">
                    Sign in with your existing workspace email and password.
                  </p>
                </div>
                <Link
                  to="/login"
                  className="inline-flex min-h-10 items-center justify-center rounded-full border border-[var(--patch-border-strong)] bg-[var(--patch-surface)] px-4 text-sm font-semibold text-[var(--patch-ink)] transition hover:bg-[var(--patch-border)] active:scale-[0.98]"
                >
                  Sign in
                </Link>
              </div>
            </motion.form>
          </div>
        </section>
        <SignupProvisioningPreview state={signupState} />
      </div>
    </main>
  );
}

type SignupProvisioningPreviewProps = {
  state: AuthFlowState;
};

const SignupProvisioningPreview = memo(function SignupProvisioningPreview({ state }: SignupProvisioningPreviewProps) {
  const statusLabel =
    state === "success" ? "workspace issued" : state === "loading" ? "provisioning account" : "ready for identity";
  const statusDetail =
    state === "success"
      ? "Session cookie accepted. Dashboard handoff is ready."
      : state === "loading"
        ? "Calling Stream 1 and preparing a private workspace shell."
        : "Create an account to unlock repository connection.";

  return (
    <section
      aria-label="Signup provisioning animation"
      className="relative flex min-h-[calc(100dvh-2rem)] items-center overflow-hidden border-x border-b border-[var(--patch-border)] bg-[var(--patch-ink)] px-4 py-8 text-white sm:px-8 lg:min-h-[calc(100dvh-4rem)] lg:rounded-r-[36px] lg:border lg:px-10 xl:px-14"
    >
      <div className="pointer-events-none absolute inset-0 opacity-35 [background-image:linear-gradient(rgba(255,255,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:52px_52px]" />
      <motion.div
        aria-hidden
        animate={{ opacity: [0.16, 0.32, 0.16], scale: [1, 1.04, 1] }}
        transition={{ duration: 7, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
        className="pointer-events-none absolute right-[-18%] top-[12%] h-[540px] w-[540px] rounded-full bg-[radial-gradient(circle,rgba(0,113,227,0.34),rgba(255,255,255,0.06)_38%,transparent_68%)]"
      />

      <motion.div
        initial={{ opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 90, damping: 20, delay: 0.12 }}
        className="relative mx-auto grid w-full max-w-[560px] gap-5 lg:ml-auto"
      >
        <div className="grid gap-2">
          <p className="text-sm font-semibold text-[var(--patch-on-dark-muted)]">Provisioning stream</p>
          <h2 className="max-w-[12ch] text-[42px] font-semibold leading-none tracking-tight text-white sm:text-[56px]">
            Account comes online.
          </h2>
        </div>

        <div className="relative overflow-hidden rounded-[38px] border border-white/10 bg-white/[0.07] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.16),0_32px_84px_-46px_rgba(0,0,0,0.72)] backdrop-blur-[18px] sm:p-6">
          <div className="grid gap-5 xl:grid-cols-[1fr_0.9fr]">
            <div className="relative mx-auto flex aspect-square w-full max-w-[300px] items-center justify-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 28, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                className="absolute inset-4 rounded-full border border-dashed border-white/20"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 20, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                className="absolute inset-12 rounded-full border border-white/10"
              />
              <motion.svg
                viewBox="0 0 220 220"
                className="absolute inset-8 text-white/35"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.35 }}
              >
                <motion.path
                  d="M110 28C62 43 38 76 42 120c4 48 42 75 91 70 38-4 67-29 72-67 5-43-19-78-59-91"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: [0.2, 1, 0.72, 1] }}
                  transition={{ duration: 6.5, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                />
              </motion.svg>

              {signupPreviewSteps.map((step, index) => {
                const Icon = step.icon;
                const positions = [
                  "left-1/2 top-2 -translate-x-1/2",
                  "right-3 top-1/2 -translate-y-1/2",
                  "bottom-3 left-1/2 -translate-x-1/2",
                  "left-3 top-1/2 -translate-y-1/2",
                ];

                return (
                  <motion.div
                    key={step.id}
                    animate={{ y: [0, -5, 0], scale: [1, 1.04, 1] }}
                    transition={{
                      duration: 3.4,
                      repeat: Number.POSITIVE_INFINITY,
                      ease: "easeInOut",
                      delay: index * 0.22,
                    }}
                    className={`absolute ${positions[index]} flex h-12 w-12 items-center justify-center rounded-[18px] border border-white/15 bg-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)] backdrop-blur-[14px]`}
                  >
                    <Icon size={18} />
                  </motion.div>
                );
              })}

              <motion.div
                layout
                className="relative grid h-36 w-36 place-items-center rounded-[34px] border border-white/15 bg-[var(--patch-surface)] p-4 text-[var(--patch-ink)] shadow-[0_26px_64px_-34px_rgba(0,0,0,0.8)]"
              >
                <motion.div
                  animate={{ opacity: [0.7, 1, 0.7], scale: [0.96, 1, 0.96] }}
                  transition={{ duration: 2.5, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                  className="flex h-14 w-14 items-center justify-center rounded-[22px] bg-[var(--patch-accent)] text-white"
                >
                  {state === "success" ? <CheckCircle2 size={24} /> : <Code2 size={24} />}
                </motion.div>
                <div className="text-center">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--patch-muted)]">
                    endpoint
                  </p>
                  <p className="mt-1 font-mono text-sm font-semibold">/auth/signup</p>
                </div>
              </motion.div>
            </div>

            <div className="grid content-center gap-3">
              {signupPreviewSteps.map((step, index) => {
                const Icon = step.icon;

                return (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, x: 24 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ type: "spring", stiffness: 110, damping: 20, delay: 0.25 + index * 0.08 }}
                    className="grid grid-cols-[auto_1fr] items-center gap-3 rounded-[22px] border border-white/10 bg-white/[0.08] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-[16px] bg-white/10 text-white">
                      <Icon size={17} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white">{step.label}</p>
                      <p className="truncate text-xs text-[var(--patch-on-dark-muted)]">{step.value}</p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            <AnimatePresence mode="wait">
              <motion.div
                key={statusLabel}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ type: "spring", stiffness: 140, damping: 20 }}
                className="rounded-[24px] border border-white/10 bg-[var(--patch-surface)] p-4 text-[var(--patch-ink)]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold">{statusLabel}</p>
                    <p className="mt-1 text-xs leading-5 text-[var(--patch-muted)]">{statusDetail}</p>
                  </div>
                  <motion.span
                    animate={{ scale: [1, 1.18, 1], opacity: [0.75, 1, 0.75] }}
                    transition={{ duration: 2.2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
                    className="mt-1 h-3 w-3 rounded-full bg-[var(--patch-accent)]"
                  />
                </div>
              </motion.div>
            </AnimatePresence>

            <div className="grid gap-2">
              {signupPreviewCards.map((card, index) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ type: "spring", stiffness: 100, damping: 20, delay: 0.44 + index * 0.08 }}
                  className="rounded-[20px] bg-white/[0.07] px-4 py-3"
                >
                  <div className="flex items-center justify-between gap-4 text-xs">
                    <span className="text-[var(--patch-on-dark-muted)]">{card.label}</span>
                    <span className="font-mono font-semibold text-white">{card.value}</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
                    <motion.div
                      animate={{ opacity: [0.55, 1, 0.55], scaleX: [0.88, 1, 0.88] }}
                      transition={{
                        duration: 2.6,
                        repeat: Number.POSITIVE_INFINITY,
                        ease: "easeInOut",
                        delay: index * 0.18,
                      }}
                      className={`h-full origin-left rounded-full bg-white ${card.width}`}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
});
