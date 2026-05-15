import { useSearch } from "@tanstack/react-router";
import { githubOauthStartUrl } from "../lib/api";

const errorMessages: Record<string, string> = {
  no_verified_email: "GitHub didn't return a verified primary email.",
  github_denied: "GitHub authorization was denied.",
  invalid_state: "OAuth state mismatch — try again.",
  missing_code: "GitHub didn't return an authorization code.",
  token_exchange_failed: "Could not exchange GitHub code for a token.",
  no_access_token: "GitHub returned no access token.",
  github_user_failed: "Could not load GitHub profile.",
  github_emails_failed: "Could not load GitHub emails.",
};

export function LoginPage() {
  const search = useSearch({ strict: false }) as { error?: string };
  const errorKey = search.error;
  const errorMessage = errorKey ? (errorMessages[errorKey] ?? "Sign-in failed.") : null;

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--patch-bg)] px-4 font-mono text-[var(--patch-fg)]">
      <div className="w-full max-w-md border border-[var(--patch-border)] bg-[var(--patch-surface)] p-6">
        <h1 className="mb-1 text-lg text-[var(--patch-accent)]">┌─ patch · sign in ─</h1>
        <p className="mb-5 text-xs text-[var(--patch-dim)]">Coding tasks → reviewable pull requests.</p>

        <a
          href={githubOauthStartUrl()}
          className="flex w-full items-center justify-center border border-[var(--patch-border-strong)] px-3 py-1.5 text-sm hover:border-[var(--patch-fg)] hover:text-[var(--patch-accent)]"
        >
          [ continue with github ]
        </a>

        {errorMessage && <p className="mt-3 text-xs text-[var(--patch-error)]">{errorMessage}</p>}

        <p className="mt-4 border-t border-[var(--patch-border)] pt-3 text-xs text-[var(--patch-dim)]">
          GitHub is the only sign-in method.
        </p>
      </div>
    </main>
  );
}
