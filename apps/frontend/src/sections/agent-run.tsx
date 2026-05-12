import { Badge, Button, Card, FileRow, SectionHeading, StatusLine } from "@patch/ui";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { AlertTriangle, CheckCircle2, Clock3, FileCode2, Loader2, MessageSquareText, Terminal } from "lucide-react";
import { useCallback } from "react";
import {
  type AgentRunEventRead,
  type AgentRunStatus,
  type AgentRunWebSocketFrame,
  apiEndpoints,
  type EventType,
  type TerminalWebSocketFrame,
} from "../lib/api";
import { useAgentRunStream } from "../lib/ws";
import { type SetActiveProps, useAgentRun, useAgentRunDiff, useAgentRunEvents } from "../wireframe-data";
import { PullRequestPanel } from "./pull-request-panel";

type AgentRunProps = SetActiveProps & {
  runId?: string;
};

type TimelineEvent = {
  key: string;
  sequence: number;
  event_type: EventType;
  payload: Record<string, unknown>;
  created_at?: string;
  source: "history" | "live";
};

const terminalStatuses: AgentRunStatus[] = ["succeeded", "failed", "cancelled"];

export function AgentRun({ runId, setActive }: AgentRunProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const agentRunQuery = useAgentRun(runId);
  const eventsQuery = useAgentRunEvents(runId, 100);
  const diffQuery = useAgentRunDiff(runId);
  const handleTerminal = useCallback(
    (frame: TerminalWebSocketFrame) => {
      if (!runId) {
        return;
      }

      queryClient.setQueryData(["patch", apiEndpoints.agentRun(runId)], (current: unknown) =>
        typeof current === "object" && current !== null ? { ...current, status: frame.status } : current,
      );
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.agentRun(runId)] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.agentRunEvents(runId, 100)] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.agentRunPullRequest(runId)] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.agentRunDiff(runId)] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.agentRuns] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.dashboard] });
    },
    [queryClient, runId],
  );
  const stream = useAgentRunStream(runId, { onTerminal: handleTerminal });

  if (!runId) {
    return (
      <Card className="p-6">
        <SectionHeading title="No Run Selected" action={<Badge>run-scoped route</Badge>} />
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--patch-muted)]">
          Create a task first, then P.A.T.C.H. will open a run-scoped page at /run/:id with live WebSocket events.
        </p>
        <Button className="mt-5" onClick={() => setActive("task")}>
          Create Agent Run
        </Button>
      </Card>
    );
  }

  if (agentRunQuery.isLoading) {
    return <AgentRunSkeleton />;
  }

  if (agentRunQuery.isError || !agentRunQuery.data) {
    return (
      <Card className="p-6">
        <SectionHeading title="Run Not Available" action={<Badge tone="inverse">error</Badge>} />
        <p className="mt-3 text-sm leading-6 text-[var(--patch-muted)]">
          The run could not be loaded. It may not exist, may belong to another user, or the session cookie expired.
        </p>
      </Card>
    );
  }

  const agentRun = agentRunQuery.data;
  const timeline = mergeTimeline(eventsQuery.data ?? [], stream.events);
  const status = stream.status ?? agentRun.status;
  const prUrl = stream.prUrl ?? agentRun.pull_request?.url ?? null;
  const latestMessage = getLatestMessage(timeline) ?? agentRun.error_message ?? "Waiting for the next agent message.";
  const diffFiles = diffQuery.data ?? [];
  const canOpenDiff = Boolean(prUrl || status === "succeeded" || diffFiles.length > 0);
  const isTerminal = terminalStatuses.includes(status);

  return (
    <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
      <div className="space-y-5">
        <Card className="p-5">
          <SectionHeading title="Run Status" action={<Badge tone="inverse">{status}</Badge>} />
          <div className="mt-5 space-y-1">
            <RunStep label="queued" reached={true} />
            <RunStep label="running" reached={status !== "queued"} />
            <RunStep label={isTerminal ? status : "terminal"} reached={isTerminal} />
          </div>
          <div className="mt-5 grid gap-3">
            <StatusLine label="Stream" value={stream.connectionStatus} />
            <StatusLine label="Run ID" value={agentRun.id} />
            <StatusLine label="Branch" value={agentRun.branch_name ?? "branch pending"} />
          </div>
        </Card>

        <PullRequestPanel
          compact
          runId={runId}
          pullRequest={agentRun.pull_request}
          branchName={agentRun.branch_name}
          status={status}
          prUrl={prUrl}
          errorMessage={
            isTerminal && status !== "succeeded"
              ? (agentRun.error_message ?? stream.error ?? "The run ended before a pull request was produced.")
              : null
          }
        />
      </div>

      <div className="space-y-5">
        <Card className="p-5">
          <SectionHeading
            title="Current Message"
            action={
              <Badge>
                <MessageSquareText size={14} />
                live tail
              </Badge>
            }
          />
          <p className="mt-5 whitespace-pre-wrap text-base leading-7 tracking-[-0.006em] text-[var(--patch-text)]">
            {latestMessage}
          </p>
          {stream.error && (
            <p className="mt-4 rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] px-4 py-3 text-sm text-[var(--patch-ink)]">
              {stream.error}
            </p>
          )}
        </Card>

        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Card surface="dark" className="overflow-hidden">
            <div className="flex items-center justify-between gap-3 border-b border-[var(--patch-dark-border)] px-5 py-4 font-semibold text-white">
              <span className="flex items-center gap-2">
                <Terminal size={18} />
                Tool Timeline
              </span>
              {stream.connectionStatus === "connecting" || stream.connectionStatus === "reconnecting" ? (
                <Loader2 size={16} className="animate-spin" />
              ) : null}
            </div>
            <div className="max-h-[440px] overflow-auto bg-[var(--patch-ink)] p-5">
              {timeline.length > 0 ? (
                <div className="space-y-3">
                  {timeline.map((event) => (
                    <TimelineRow key={event.key} event={event} />
                  ))}
                </div>
              ) : (
                <pre className="text-xs leading-6 text-white">Waiting for live events...</pre>
              )}
            </div>
          </Card>

          <Card className="p-5">
            <SectionHeading title="Changed Files" action={<FileCode2 size={18} />} />
            <div className="mt-5 space-y-3 text-sm">
              {diffFiles.length > 0 ? (
                diffFiles.map((file) => (
                  <FileRow
                    key={file.file_path}
                    path={file.file_path}
                    additions={`+${file.additions}`}
                    deletions={`-${file.deletions}`}
                  />
                ))
              ) : (
                <p className="rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm leading-6 text-[var(--patch-muted)]">
                  {diffQuery.isError ? "Diff is not available yet." : "Changed files appear after GitHub diff fetch."}
                </p>
              )}
            </div>
            <Button
              className="mt-5 w-full"
              disabled={!canOpenDiff}
              onClick={() => {
                if (runId) {
                  void navigate({ to: "/run/$id/diff", params: { id: runId } });
                }
              }}
            >
              Open Diff Review
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}

function AgentRunSkeleton() {
  return (
    <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
      <Card className="p-5">
        <div className="h-7 w-40 rounded-full bg-[var(--patch-border)]" />
        <div className="mt-6 space-y-3">
          <div className="h-16 rounded-[18px] bg-[var(--patch-bg)]" />
          <div className="h-16 rounded-[18px] bg-[var(--patch-bg)]" />
          <div className="h-16 rounded-[18px] bg-[var(--patch-bg)]" />
        </div>
      </Card>
      <Card className="p-5">
        <div className="h-7 w-48 rounded-full bg-[var(--patch-border)]" />
        <div className="mt-6 h-64 rounded-[18px] bg-[var(--patch-bg)]" />
      </Card>
    </div>
  );
}

function RunStep({ label, reached }: { label: string; reached: boolean }) {
  return (
    <div className="flex gap-3 rounded-[18px] px-2 py-3">
      <div
        className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          reached
            ? "bg-[var(--patch-ink)] text-white"
            : "border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-muted)]"
        }`}
      >
        {reached ? <CheckCircle2 size={16} /> : <Clock3 size={16} />}
      </div>
      <div>
        <div className="text-sm font-semibold tracking-[-0.003em] text-[var(--patch-ink)]">{label}</div>
        <div className="text-sm text-[var(--patch-muted)]">{reached ? "Reached" : "Waiting"}</div>
      </div>
    </div>
  );
}

function TimelineRow({ event }: { event: TimelineEvent }) {
  const toolName = getPayloadText(event.payload, "tool_name");
  const title = toolName ?? event.event_type;
  const detail =
    getPayloadText(event.payload, "text") ??
    getPayloadText(event.payload, "message") ??
    getPayloadText(event.payload, "tool_output") ??
    formatUnknown(event.payload.tool_input) ??
    formatUnknown(event.payload);
  const isError = event.event_type === "error";

  return (
    <div className="rounded-[16px] border border-[var(--patch-dark-border)] bg-[var(--patch-on-dark-panel)] p-3">
      <div className="flex items-center justify-between gap-3 text-xs font-semibold text-white">
        <span className="flex min-w-0 items-center gap-2">
          {isError ? <AlertTriangle size={14} /> : <Terminal size={14} />}
          <span className="truncate">{title}</span>
        </span>
        <span className="font-mono text-[var(--patch-on-dark-muted)]">#{event.sequence}</span>
      </div>
      <pre className="mt-2 whitespace-pre-wrap break-words text-xs leading-5 text-[var(--patch-on-dark-muted)]">
        {detail}
      </pre>
    </div>
  );
}

function mergeTimeline(historyEvents: AgentRunEventRead[], liveEvents: AgentRunWebSocketFrame[]): TimelineEvent[] {
  const timelineBySequence = new Map<number, TimelineEvent>();

  for (const event of historyEvents) {
    timelineBySequence.set(event.sequence, {
      key: `history-${event.sequence}`,
      sequence: event.sequence,
      event_type: event.event_type,
      payload: event.payload,
      created_at: event.created_at,
      source: "history",
    });
  }

  for (const event of liveEvents) {
    timelineBySequence.set(event.sequence, {
      key: `live-${event.sequence}`,
      sequence: event.sequence,
      event_type: event.type,
      payload: event.payload,
      source: "live",
    });
  }

  return Array.from(timelineBySequence.values()).sort((left, right) => left.sequence - right.sequence);
}

function getLatestMessage(events: TimelineEvent[]) {
  const reversedEvents = [...events].reverse();
  const messageEvent = reversedEvents.find(
    (event) => event.event_type === "message" || event.event_type === "summary" || event.event_type === "plan",
  );
  const errorEvent = reversedEvents.find((event) => event.event_type === "error");

  return getPayloadText(messageEvent?.payload, "text") ?? getPayloadText(errorEvent?.payload, "message");
}

function getPayloadText(payload: Record<string, unknown> | undefined, key: string) {
  const value = payload?.[key];

  return typeof value === "string" ? value : null;
}

function formatUnknown(value: unknown) {
  if (typeof value === "string") {
    return value;
  }

  if (!value) {
    return null;
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
