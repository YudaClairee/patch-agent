import { cn, patchClasses } from "@patch/ui";
import { Link, useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Eye, EyeOff, GitBranch, KeyRound, Mail, ShieldCheck, UserPlus } from "lucide-react";
import { type FormEvent, useState } from "react";
import { patchApi } from "../lib/api";
import { type AuthFlowState, AuthSubmitButton, AuthWorkspacePreview, FormField } from "./auth-components";

type LoginState = AuthFlowState;

const signInOptions = ["GitHub", "GitLab", "SSO"] as const;

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
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

              <AuthSubmitButton
                state={loginState}
                idleLabel="Sign in"
                loadingLabel="Verifying workspace"
                successLabel="Workspace ready"
              />

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

              <div className="mt-5 flex flex-col gap-3 border-t border-[var(--patch-border)] pt-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-[var(--patch-ink)]">New workspace?</p>
                  <p className="mt-1 text-xs leading-5 text-[var(--patch-muted)]">
                    Create an account and receive the auth cookie from Stream 1.
                  </p>
                </div>
                <Link
                  to="/signup"
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-full border border-[var(--patch-border-strong)] bg-[var(--patch-surface)] px-4 text-sm font-semibold text-[var(--patch-ink)] transition hover:bg-[var(--patch-border)] active:scale-[0.98]"
                >
                  <UserPlus size={16} />
                  Sign up
                </Link>
              </div>
            </motion.form>
          </div>
        </section>
        <AuthWorkspacePreview state={loginState} rememberWorkspace={rememberWorkspace} />
      </div>
    </main>
  );
}
