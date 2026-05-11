import { Badge, Button, Card, FileRow, SectionHeading } from "@patch/ui";
import { CheckCircle2, Clock3, Terminal } from "lucide-react";
import { type SetActiveProps, statusSteps, useAgentRun, useAgentRunDiff, useAgentRunEvents } from "../wireframe-data";

export function AgentRun({ setActive }: SetActiveProps) {
  const { data: agentRun } = useAgentRun();
  const { data: events } = useAgentRunEvents(agentRun.id);
  const { data: diffFiles } = useAgentRunDiff(agentRun.id);
  const currentStatusIndex = statusSteps.indexOf(agentRun.status);
  const planText = getPayloadText(events.find((event) => event.event_type === "plan")?.payload, "text");
  const toolLogs = events
    .filter((event) => event.event_type === "tool_result")
    .map((event) => {
      const toolName = getPayloadText(event.payload, "tool_name") ?? "tool";
      const toolOutput = getPayloadText(event.payload, "tool_output") ?? "completed";

      return `$ ${toolName}\n${toolOutput}`;
    });

  return (
    <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
      <Card className="p-5">
        <SectionHeading title="Run Status" action={<Badge tone="inverse">{agentRun.status}</Badge>} />
        <div className="mt-5 space-y-1">
          {statusSteps.map((step, index) => (
            <div key={step} className="flex gap-3 rounded-[18px] px-2 py-3">
              <div
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${index <= currentStatusIndex ? "bg-[var(--patch-ink)] text-white" : "border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-muted)]"}`}
              >
                {index <= currentStatusIndex ? <CheckCircle2 size={16} /> : <Clock3 size={16} />}
              </div>
              <div>
                <div className="text-sm font-semibold tracking-[-0.003em] text-[var(--patch-ink)]">{step}</div>
                <div className="text-sm text-[var(--patch-muted)]">
                  {index <= currentStatusIndex ? "Reached" : "Waiting"}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <div className="space-y-5">
        <Card className="p-5">
          <SectionHeading title="Agent Plan" />
          <ol className="mt-5 space-y-2 text-base leading-6 tracking-[-0.006em] text-[var(--patch-text)]">
            {(planText?.split(", ") ?? ["Waiting for plan event from /agent_runs/{id}/events."]).map((step, index) => (
              <li key={step}>
                {index + 1}. {step}
              </li>
            ))}
          </ol>
        </Card>

        <div className="grid gap-5 lg:grid-cols-2">
          <Card surface="dark" className="overflow-hidden">
            <div className="flex items-center gap-2 border-b border-[var(--patch-dark-border)] px-5 py-4 font-semibold text-white">
              <Terminal size={18} />
              Command Logs
            </div>
            <pre className="h-52 overflow-auto bg-[var(--patch-ink)] p-5 text-xs leading-6 text-white">
              {toolLogs.length > 0 ? toolLogs.join("\n\n") : "Waiting for tool_result events..."}
            </pre>
          </Card>
          <Card className="p-5">
            <SectionHeading title="Changed Files" />
            <div className="mt-5 space-y-3 text-sm">
              {diffFiles.map((file) => (
                <FileRow
                  key={file.file_path}
                  path={file.file_path}
                  additions={`+${file.additions}`}
                  deletions={`-${file.deletions}`}
                />
              ))}
            </div>
            <Button className="mt-5 w-full" onClick={() => setActive("diff")}>
              Open Diff Review
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}

function getPayloadText(payload: Record<string, unknown> | undefined, key: string) {
  const value = payload?.[key];

  return typeof value === "string" ? value : null;
}
