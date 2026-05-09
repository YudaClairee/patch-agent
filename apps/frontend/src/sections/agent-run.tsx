import { Badge, Button, Card, FileRow, SectionHeading } from "@patch/ui";
import { CheckCircle2, Clock3, Terminal } from "lucide-react";
import { type SetActiveProps, statusSteps } from "../wireframe-data";

export function AgentRun({ setActive }: SetActiveProps) {
  return (
    <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
      <Card className="p-5">
        <SectionHeading title="Run Status" action={<Badge tone="inverse">verifying</Badge>} />
        <div className="mt-5 space-y-1">
          {statusSteps.map((step, index) => (
            <div key={step} className="flex gap-3 rounded-[18px] px-2 py-3">
              <div
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${index <= 5 ? "bg-[var(--patch-ink)] text-white" : "border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-muted)]"}`}
              >
                {index <= 5 ? <CheckCircle2 size={16} /> : <Clock3 size={16} />}
              </div>
              <div>
                <div className="text-sm font-semibold tracking-[-0.003em] text-[var(--patch-ink)]">{step}</div>
                <div className="text-sm text-[var(--patch-muted)]">{index <= 5 ? "Completed" : "Waiting"}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <div className="space-y-5">
        <Card className="p-5">
          <SectionHeading title="Agent Plan" />
          <ol className="mt-5 space-y-2 text-base leading-6 tracking-[-0.006em] text-[var(--patch-text)]">
            <li>1. Inspect repository structure.</li>
            <li>2. Search files related to authentication and login.</li>
            <li>3. Read existing router and test files.</li>
            <li>4. Add unit tests for login success and invalid password.</li>
            <li>5. Run pytest and ruff check.</li>
            <li>6. Generate git diff for review.</li>
          </ol>
        </Card>

        <div className="grid gap-5 lg:grid-cols-2">
          <Card surface="dark" className="overflow-hidden">
            <div className="flex items-center gap-2 border-b border-[var(--patch-dark-border)] px-5 py-4 font-semibold text-white">
              <Terminal size={18} />
              Command Logs
            </div>
            <pre className="h-52 overflow-auto bg-[var(--patch-ink)] p-5 text-xs leading-6 text-white">{`$ uv run pytest
12 passed in 2.41s

$ uv run ruff check .
All checks passed!`}</pre>
          </Card>
          <Card className="p-5">
            <SectionHeading title="Changed Files" />
            <div className="mt-5 space-y-3 text-sm">
              <FileRow path="tests/test_auth.py" additions="+82" deletions="-0" />
              <FileRow path="app/auth/routes.py" additions="+4" deletions="-1" />
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
