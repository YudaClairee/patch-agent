import { Badge, Button, Card, Field, SectionHeading, Textarea } from "@patch/ui";
import { GitBranch, Play } from "lucide-react";
import type { SetActiveProps } from "../wireframe-data";

export function NewTask({ setActive }: SetActiveProps) {
  return (
    <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
      <Card className="p-5">
        <SectionHeading title="Task Configuration" />
        <div className="mt-5 space-y-4">
          <Field label="Repository" placeholder="fastapi-auth-app" />
          <Field label="Target Branch" placeholder="main" icon={<GitBranch size={16} />} />
          <Field label="Setup Command Override" placeholder="Optional" />
          <Field label="Test Command Override" placeholder="uv run pytest" />
          <Field label="Lint Command Override" placeholder="uv run ruff check ." />
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="flex min-h-14 items-center justify-between gap-3 border-b border-[var(--patch-border)] px-5">
          <SectionHeading title="Instruction" />
          <Badge>draft</Badge>
        </div>
        <Textarea
          className="h-[360px] w-full resize-none bg-[var(--patch-surface)] p-5 text-base leading-7 tracking-[-0.006em] text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
          defaultValue={
            "Tambahkan unit test untuk endpoint login. Pastikan test dapat dijalankan dengan pytest. Jangan ubah logic utama jika tidak perlu."
          }
        />
        <div className="flex justify-end gap-3 border-t border-[var(--patch-border)] bg-[var(--patch-bg)] px-5 py-4">
          <Button variant="secondary" onClick={() => setActive("dashboard")}>
            Save Draft
          </Button>
          <Button onClick={() => setActive("run")}>
            <Play size={15} />
            Create Agent Run
          </Button>
        </div>
      </Card>
    </div>
  );
}
