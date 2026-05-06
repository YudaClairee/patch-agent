import { Button, Card, Field, SectionHeading, StatusLine } from "@patch/ui";
import { FolderGit, GitBranch, ShieldCheck } from "lucide-react";
import type { SetActiveProps } from "../wireframe-data";

export function RepositorySetup({ setActive }: SetActiveProps) {
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <Card className="p-5 md:p-6">
        <SectionHeading title="Connection" />
        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <Field label="Repository Name" placeholder="fastapi-auth-app" />
          <Field label="Repository URL" placeholder="git@github.com:user/fastapi-auth-app.git" />
          <Field label="Default Branch" placeholder="main" icon={<GitBranch size={16} />} />
          <Field label="Credential Ref" placeholder="github_token_prod_01" secure />
          <Field label="Setup Command" placeholder="uv sync" />
          <Field label="Test Command" placeholder="uv run pytest" />
          <Field label="Lint Command" placeholder="uv run ruff check ." />
          <Field label="Working Directory" placeholder="./" />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setActive("dashboard")}>
            Cancel
          </Button>
          <Button onClick={() => setActive("task")}>
            <FolderGit size={15} />
            Save Repository
          </Button>
        </div>
      </Card>

      <Card surface="dark" className="p-5">
        <div className="flex items-center gap-2 text-base font-semibold">
          <ShieldCheck size={18} />
          Credential Safety
        </div>
        <p className="mt-3 text-sm leading-6 text-[var(--patch-on-dark-muted)]">
          Token dan private key tidak ditampilkan ulang. UI hanya menyimpan reference credential.
        </p>
        <div className="mt-6 space-y-3">
          <StatusLine label="Secret visibility" value="hidden" tone="dark" />
          <StatusLine label="Review mode" value="required" tone="dark" />
          <StatusLine label="Branch policy" value="protected" tone="dark" />
        </div>
      </Card>
    </div>
  );
}
