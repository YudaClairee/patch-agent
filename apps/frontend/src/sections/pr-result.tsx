import { Badge, Card, SectionHeading } from "@patch/ui";
import { useAgentRun, useAgentRunPullRequest } from "../wireframe-data";
import { PullRequestPanel } from "./pull-request-panel";

type PRResultProps = {
  runId?: string;
};

export function PRResult({ runId }: PRResultProps) {
  const agentRunQuery = useAgentRun(runId);
  const pullRequestQuery = useAgentRunPullRequest(runId);
  const agentRun = agentRunQuery.data;
  const pullRequest = pullRequestQuery.data ?? agentRun?.pull_request ?? null;

  if (!runId) {
    return (
      <Card className="p-6">
        <SectionHeading title="No Run Selected" action={<Badge>PR route</Badge>} />
        <p className="mt-3 text-sm leading-6 text-[var(--patch-muted)]">
          Open a run-scoped PR route after a successful agent run.
        </p>
      </Card>
    );
  }

  return (
    <PullRequestPanel
      runId={runId}
      pullRequest={pullRequest}
      branchName={agentRun?.branch_name}
      status={agentRun?.status}
      errorMessage={agentRun?.error_message}
    />
  );
}
