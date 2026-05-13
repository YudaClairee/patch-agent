import { Badge, Button, Card, FileRow, SectionHeading, Textarea } from "@patch/ui";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ExternalLink, GitPullRequest, Loader2, MessageSquarePlus } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { apiEndpoints, type FeedbackCreate, patchApi } from "../lib/api";
import { type SetActiveProps, useAgentRun, useAgentRunDiff, useAgentRunPullRequest } from "../wireframe-data";

type SubmitState = "idle" | "submitting" | "success" | "error";

type DiffReviewProps = SetActiveProps & {
  runId?: string;
};

type DiffRow = {
  id: string;
  left: string;
  right: string;
  tone: "context" | "added" | "removed" | "hunk";
};

export function DiffReview({ runId, setActive }: DiffReviewProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const agentRunQuery = useAgentRun(runId);
  const diffQuery = useAgentRunDiff(runId);
  const pullRequestQuery = useAgentRunPullRequest(runId);
  const diffFiles = diffQuery.data ?? [];
  const [activePath, setActivePath] = useState<string | null>(null);
  const [instruction, setInstruction] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const activeFile = diffFiles.find((file) => file.file_path === activePath) ?? diffFiles[0] ?? null;
  const pullRequest = pullRequestQuery.data ?? agentRunQuery.data?.pull_request ?? null;
  const diffRows = useMemo(() => parseUnifiedDiff(activeFile?.patch), [activeFile?.patch]);

  const handleFeedbackSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!runId) {
      setSubmitState("error");
      return;
    }

    const feedbackCreate: FeedbackCreate = {
      instruction: instruction.trim(),
    };

    if (!feedbackCreate.instruction) {
      setSubmitState("error");
      return;
    }

    setSubmitState("submitting");

    try {
      const childRun = await patchApi.submitFeedback(runId, feedbackCreate);
      setSubmitState("success");
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.agentRuns] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.dashboard] });
      void navigate({ to: "/run/$id", params: { id: childRun.id } });
    } catch {
      setSubmitState("error");
    }
  };

  if (!runId) {
    return (
      <Card className="p-6">
        <SectionHeading title="No Run Selected" action={<Badge>diff route</Badge>} />
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--patch-muted)]">
          Open a completed run first, then use its run-scoped diff route to review GitHub changes.
        </p>
        <Button className="mt-5" onClick={() => setActive("task")}>
          Create Agent Run
        </Button>
      </Card>
    );
  }

  return (
    <div className="flex min-h-[calc(100dvh-180px)] flex-col gap-5">
      <Card className="p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <GitPullRequest size={18} className="text-[var(--patch-muted)]" />
              <h2 className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-[var(--patch-ink)]">
                {pullRequest?.title ?? "Pull request diff"}
              </h2>
              <Badge tone="inverse">{pullRequest?.state ?? agentRunQuery.data?.status ?? "loading"}</Badge>
            </div>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--patch-muted)]">
              Review the GitHub diff fetched on demand for run {runId}. Follow-up feedback creates a child run on the
              same PR branch.
            </p>
          </div>
          {pullRequest?.url && (
            <a
              href={pullRequest.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-full border border-[var(--patch-border-strong)] bg-[var(--patch-surface)] px-4 text-sm font-semibold text-[var(--patch-ink)] transition hover:bg-[var(--patch-bg)]"
            >
              View on GitHub
              <ExternalLink size={15} />
            </a>
          )}
        </div>
      </Card>

      <div className="grid min-h-0 flex-1 gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Card className="min-h-0 p-5">
          <SectionHeading title="Files" action={<Badge>{diffFiles.length}</Badge>} />
          <div className="mt-5 space-y-3 overflow-auto pr-1">
            {diffQuery.isLoading && (
              <div className="flex items-center gap-2 rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm text-[var(--patch-muted)]">
                <Loader2 size={16} className="animate-spin" />
                Loading diff files
              </div>
            )}
            {diffQuery.isError && (
              <p className="rounded-[18px] border border-[var(--patch-border-strong)] bg-[var(--patch-bg)] p-4 text-sm leading-6 text-[var(--patch-ink)]">
                Diff is unavailable. Check GitHub credential access or wait until the PR exists.
              </p>
            )}
            {!diffQuery.isLoading && !diffQuery.isError && diffFiles.length === 0 && (
              <p className="rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm leading-6 text-[var(--patch-muted)]">
                No changed files returned by GitHub.
              </p>
            )}
            {diffFiles.map((file) => (
              <button
                key={file.file_path}
                type="button"
                onClick={() => setActivePath(file.file_path)}
                className={`block w-full rounded-[20px] text-left transition ${
                  activeFile?.file_path === file.file_path
                    ? "outline outline-2 outline-[var(--patch-ink)]"
                    : "hover:bg-[var(--patch-bg)]"
                }`}
              >
                <FileRow path={file.file_path} additions={`+${file.additions}`} deletions={`-${file.deletions}`} />
              </button>
            ))}
          </div>
        </Card>

        <Card className="min-h-0 overflow-hidden">
          <div className="flex min-h-14 items-center justify-between gap-3 border-b border-[var(--patch-border)] px-5">
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-[var(--patch-ink)]">
                {activeFile?.file_path ?? "No file selected"}
              </div>
              <div className="text-xs text-[var(--patch-muted)]">{activeFile?.status ?? "diff"}</div>
            </div>
            {activeFile && (
              <Badge>
                +{activeFile.additions} / -{activeFile.deletions}
              </Badge>
            )}
          </div>
          <div className="h-[520px] overflow-auto bg-[var(--patch-bg)]">
            {activeFile?.patch ? (
              <SplitDiff rows={diffRows} />
            ) : (
              <div className="grid h-full place-items-center p-6">
                <p className="max-w-md text-center text-sm leading-6 text-[var(--patch-muted)]">
                  {activeFile
                    ? "GitHub did not return a textual patch for this file. It may be binary, renamed, or too large."
                    : "Select a file to inspect its patch."}
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      <form
        className="sticky bottom-0 rounded-[24px] border border-[var(--patch-border)] bg-[var(--patch-surface)] p-4 shadow-[var(--patch-shadow-floating)]"
        onSubmit={handleFeedbackSubmit}
      >
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <label className="block" htmlFor="feedback-instruction">
            <div className="mb-2 text-sm font-semibold text-[var(--patch-ink)]">Request follow-up changes</div>
            <Textarea
              id="feedback-instruction"
              name="instruction"
              className="min-h-24 w-full rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm leading-6"
              value={instruction}
              onChange={(event) => {
                setInstruction(event.target.value);
                if (submitState === "error") {
                  setSubmitState("idle");
                }
              }}
              placeholder="Describe the follow-up changes for this pull request branch"
            />
          </label>
          <div className="grid gap-2 sm:grid-cols-2 lg:w-[320px]">
            <Button
              variant="secondary"
              disabled={!pullRequest?.url}
              onClick={() => {
                if (pullRequest?.url) {
                  window.open(pullRequest.url, "_blank", "noopener,noreferrer");
                }
              }}
            >
              Accept / View PR
            </Button>
            <Button type="submit" disabled={submitState === "submitting"}>
              <MessageSquarePlus size={15} />
              {submitState === "submitting" ? "Submitting..." : "Request Changes"}
            </Button>
          </div>
        </div>
        {submitState === "error" && (
          <p className="mt-3 text-sm text-[var(--patch-ink)]">
            Feedback needs an instruction and the parent run must be succeeded.
          </p>
        )}
      </form>
    </div>
  );
}

function SplitDiff({ rows }: { rows: DiffRow[] }) {
  return (
    <div className="min-w-[760px] font-mono text-xs leading-5">
      <div className="sticky top-0 grid grid-cols-2 border-b border-[var(--patch-border)] bg-[var(--patch-surface)] text-[var(--patch-muted)]">
        <div className="border-r border-[var(--patch-border)] px-4 py-2">Before</div>
        <div className="px-4 py-2">After</div>
      </div>
      {rows.map((row) => (
        <div key={row.id} className={`grid grid-cols-2 ${rowClassName(row.tone)}`}>
          <pre className="min-h-7 whitespace-pre-wrap break-words border-r border-[var(--patch-border)] px-4 py-1.5">
            {row.left}
          </pre>
          <pre className="min-h-7 whitespace-pre-wrap break-words px-4 py-1.5">{row.right}</pre>
        </div>
      ))}
    </div>
  );
}

function parseUnifiedDiff(patch: string | null | undefined): DiffRow[] {
  if (!patch) {
    return [];
  }

  return patch.split("\n").map((line, index) => {
    if (line.startsWith("@@")) {
      return { id: `${index}-hunk`, left: line, right: line, tone: "hunk" };
    }

    if (line.startsWith("+")) {
      return { id: `${index}-added`, left: "", right: line.slice(1), tone: "added" };
    }

    if (line.startsWith("-")) {
      return { id: `${index}-removed`, left: line.slice(1), right: "", tone: "removed" };
    }

    const text = line.startsWith(" ") ? line.slice(1) : line;

    return { id: `${index}-context`, left: text, right: text, tone: "context" };
  });
}

function rowClassName(tone: DiffRow["tone"]) {
  if (tone === "added") {
    return "bg-[rgba(52,199,89,0.11)] text-[var(--patch-ink)]";
  }

  if (tone === "removed") {
    return "bg-[rgba(255,59,48,0.1)] text-[var(--patch-ink)]";
  }

  if (tone === "hunk") {
    return "bg-[var(--patch-surface)] text-[var(--patch-muted)]";
  }

  return "bg-[var(--patch-bg)] text-[var(--patch-text)]";
}
