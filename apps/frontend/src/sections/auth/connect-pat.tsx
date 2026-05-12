import { Badge, Button, Card, Field, SectionHeading, StatusLine } from "@patch/ui";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Loader2, ShieldCheck, Trash2 } from "lucide-react";
import { type FormEvent, useState } from "react";
import { apiEndpoints, type GitHubCredentialRead, patchApi } from "../../lib/api";
import { useGitHubCredentials } from "../../wireframe-data";

type RequestState = "idle" | "loading" | "success" | "error";

export function ConnectPat() {
  const queryClient = useQueryClient();
  const meQuery = useQuery({
    queryKey: ["patch", apiEndpoints.me],
    queryFn: patchApi.getMe,
    retry: false,
  });
  const credentialsQuery = useGitHubCredentials();
  const credentials = credentialsQuery.data ?? [];
  const [token, setToken] = useState("");
  const [connectState, setConnectState] = useState<RequestState>("idle");
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleConnect = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!token.trim()) {
      setConnectState("error");
      setMessage("Paste a GitHub PAT before saving.");
      return;
    }

    setConnectState("loading");
    setMessage(null);

    try {
      await patchApi.createGitHubCredential({ token: token.trim() });
      setToken("");
      setConnectState("success");
      setMessage("GitHub PAT saved. Diff fetches can now use the encrypted credential.");
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.me] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.githubCredentials] });
    } catch (error) {
      setConnectState("error");
      setMessage(error instanceof Error ? error.message : "GitHub PAT could not be saved.");
    }
  };

  const handleRevoke = async (credential: GitHubCredentialRead) => {
    setRevokingId(credential.id);
    setMessage(null);

    try {
      await patchApi.deleteGitHubCredential(credential.id);
      setMessage(`GitHub credential for ${credential.github_username} revoked.`);
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.me] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.githubCredentials] });
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "GitHub credential could not be revoked.");
    } finally {
      setRevokingId(null);
    }
  };

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-5">
        <Card className="p-5 md:p-6">
          <form onSubmit={handleConnect}>
            <SectionHeading title="Connect GitHub PAT" action={<Badge>{apiEndpoints.githubCredentials}</Badge>} />
            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--patch-muted)]">
              The token is sent once to Stream 1 and stored encrypted by the backend. The browser clears the input after
              a successful save.
            </p>
            <div className="mt-5">
              <Field
                label="GitHub personal access token"
                name="token"
                placeholder="ghp_..."
                value={token}
                onChange={(event) => {
                  setToken(event.target.value);
                  if (connectState === "error") {
                    setConnectState("idle");
                  }
                }}
                icon={<KeyRound size={16} />}
                secure
                required
              />
            </div>
            <div className="mt-6 flex justify-end">
              <Button type="submit" disabled={connectState === "loading"}>
                {connectState === "loading" ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <ShieldCheck size={15} />
                )}
                Save PAT
              </Button>
            </div>
          </form>
        </Card>

        <Card className="p-5 md:p-6">
          <SectionHeading title="Saved Credentials" action={<Badge>GET</Badge>} />
          <div className="mt-5 space-y-3">
            {credentialsQuery.isLoading && (
              <p className="rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm text-[var(--patch-muted)]">
                Loading GitHub credentials...
              </p>
            )}
            {credentialsQuery.isError && (
              <p className="rounded-[18px] border border-[var(--patch-border-strong)] bg-[var(--patch-bg)] p-4 text-sm text-[var(--patch-ink)]">
                Unable to load GitHub credentials.
              </p>
            )}
            {!credentialsQuery.isLoading && !credentialsQuery.isError && credentials.length === 0 && (
              <p className="rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm text-[var(--patch-muted)]">
                No GitHub credential is connected yet.
              </p>
            )}
            {credentials.map((credential) => (
              <div
                key={credential.id}
                className="rounded-[20px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-[var(--patch-ink)]">
                      {credential.github_username}
                    </div>
                    <div className="mt-1 text-xs leading-5 text-[var(--patch-muted)]">
                      {credential.token_scopes || "scopes unavailable"} / last used{" "}
                      {formatCredentialDate(credential.last_used_at)}
                    </div>
                  </div>
                  <Button
                    variant="danger"
                    disabled={revokingId === credential.id}
                    onClick={() => void handleRevoke(credential)}
                  >
                    {revokingId === credential.id ? (
                      <Loader2 size={15} className="animate-spin" />
                    ) : (
                      <Trash2 size={15} />
                    )}
                    Revoke
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card surface="dark" className="p-5">
        <div className="flex items-center gap-2 text-base font-semibold text-white">
          <ShieldCheck size={18} />
          Credential Status
        </div>
        <div className="mt-5 space-y-3">
          <StatusLine label="Current user" value={meQuery.data?.email ?? "not loaded"} tone="dark" />
          <StatusLine
            label="Profile"
            value={meQuery.isLoading ? "loading" : meQuery.isError ? "session unavailable" : "session active"}
            tone="dark"
          />
          <StatusLine label="Diff dependency" value="GitHub PAT required for /agent_runs/{id}/diff" tone="dark" />
        </div>
        {message && (
          <p className="mt-5 rounded-[18px] border border-[var(--patch-dark-border)] bg-[var(--patch-on-dark-panel)] px-4 py-3 text-sm leading-6 text-white">
            {message}
          </p>
        )}
      </Card>
    </div>
  );
}

function formatCredentialDate(value: string | null) {
  if (!value) {
    return "never";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
