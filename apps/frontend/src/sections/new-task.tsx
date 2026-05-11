import { Badge, Button, Card, Field, SectionHeading, Textarea } from "@patch/ui";
import { GitBranch, Play } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { apiEndpoints, patchApi, type TaskCreate } from "../api-contract";
import { repositoryLabel, type SetActiveProps, useRepositories } from "../wireframe-data";

type SubmitState = "idle" | "submitting" | "success" | "error";

export function NewTask({ setActive }: SetActiveProps) {
  const { data: repositories } = useRepositories();
  const firstRepository = repositories[0];
  const [repository_id, setRepositoryId] = useState(firstRepository?.id ?? "");
  const [target_branch, setTargetBranch] = useState(firstRepository?.default_branch ?? "main");
  const [instruction, setInstruction] = useState(
    "Tambahkan unit test untuk endpoint login. Pastikan test dapat dijalankan dengan pytest. Jangan ubah logic utama jika tidak perlu.",
  );
  const [submitState, setSubmitState] = useState<SubmitState>("idle");

  useEffect(() => {
    if (!repository_id && firstRepository) {
      setRepositoryId(firstRepository.id);
      setTargetBranch(firstRepository.default_branch);
    }
  }, [firstRepository, repository_id]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const taskCreate: TaskCreate = {
      repository_id,
      instruction: instruction.trim(),
      target_branch: target_branch.trim(),
    };

    if (!taskCreate.repository_id || !taskCreate.instruction || !taskCreate.target_branch) {
      setSubmitState("error");
      return;
    }

    setSubmitState("submitting");

    try {
      await patchApi.createTask(taskCreate);
      setSubmitState("success");
      setActive("run");
    } catch {
      setSubmitState("error");
    }
  };

  return (
    <form className="grid gap-5 xl:grid-cols-[360px_1fr]" onSubmit={handleSubmit}>
      <Card className="p-5">
        <SectionHeading title="TaskCreate" action={<Badge>{apiEndpoints.tasks}</Badge>} />
        <div className="mt-5 space-y-4">
          <label className="block">
            <div className="mb-2 text-sm font-semibold tracking-[-0.003em] text-[var(--patch-ink)]">repository_id</div>
            <select
              name="repository_id"
              value={repository_id}
              onChange={(event) => {
                const selectedRepository = repositories.find((repository) => repository.id === event.target.value);
                setRepositoryId(event.target.value);
                setTargetBranch(selectedRepository?.default_branch ?? target_branch);
              }}
              className="flex min-h-11 w-full items-center rounded-[16px] border border-[var(--patch-border)] bg-[var(--patch-bg)] px-3 text-sm text-[var(--patch-ink)] outline-none transition focus:border-[var(--patch-ink)]"
              required
            >
              {repositories.map((repository) => (
                <option key={repository.id} value={repository.id}>
                  {repositoryLabel(repository)}
                </option>
              ))}
            </select>
          </label>
          <Field
            label="target_branch"
            name="target_branch"
            placeholder="main"
            value={target_branch}
            onChange={(event) => setTargetBranch(event.target.value)}
            icon={<GitBranch size={16} />}
            required
          />
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="flex min-h-14 items-center justify-between gap-3 border-b border-[var(--patch-border)] px-5">
          <SectionHeading title="instruction" />
          <Badge>TaskCreate</Badge>
        </div>
        <Textarea
          name="instruction"
          className="h-[360px] w-full resize-none bg-[var(--patch-surface)] p-5 text-base leading-7 tracking-[-0.006em] text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
          value={instruction}
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="Describe the coding task"
          required
        />
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--patch-border)] bg-[var(--patch-bg)] px-5 py-4">
          {submitState === "error" ? (
            <p className="text-sm text-[var(--patch-ink)]">
              POST /tasks gagal. Cek repository_id, instruction, dan target_branch.
            </p>
          ) : (
            <p className="text-sm text-[var(--patch-muted)]">Response: AgentRunRead (201)</p>
          )}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setActive("dashboard")}>
              Save Draft
            </Button>
            <Button type="submit" disabled={submitState === "submitting"}>
              <Play size={15} />
              {submitState === "submitting" ? "Creating..." : "Create Agent Run"}
            </Button>
          </div>
        </div>
      </Card>
    </form>
  );
}
