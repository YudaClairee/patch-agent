import { Badge, Button, Card, Field, SectionHeading, Textarea } from "@patch/ui";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { GitBranch, Play } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { apiEndpoints, patchApi, type TaskCreate } from "../lib/api";
import { repositoryLabel, type SetActiveProps, useRepositories } from "../wireframe-data";

type SubmitState = "idle" | "submitting" | "success" | "error";

export function NewTask({ setActive }: SetActiveProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: repositories = [], isLoading, isError } = useRepositories();
  const firstRepository = repositories[0];
  const [repository_id, setRepositoryId] = useState(firstRepository?.id ?? "");
  const [target_branch, setTargetBranch] = useState(firstRepository?.default_branch ?? "main");
  const [instruction, setInstruction] = useState("");
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
      const agentRun = await patchApi.createTask(taskCreate);
      setSubmitState("success");
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.tasks] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.agentRuns] });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.dashboard] });
      void navigate({ to: "/run/$id", params: { id: agentRun.id } });
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
              disabled={isLoading || repositories.length === 0}
            >
              {repositories.map((repository) => (
                <option key={repository.id} value={repository.id}>
                  {repositoryLabel(repository)}
                </option>
              ))}
            </select>
            {repositories.length === 0 && (
              <p className="mt-2 text-xs leading-5 text-[var(--patch-muted)]">
                {isLoading
                  ? "Loading connected repositories..."
                  : "No repository is connected yet. Add one before creating a run."}
              </p>
            )}
            {isError && (
              <p className="mt-2 text-xs leading-5 text-[var(--patch-ink)]">
                Unable to load repositories from Stream 2.
              </p>
            )}
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
            <Button type="submit" disabled={submitState === "submitting" || repositories.length === 0}>
              <Play size={15} />
              {submitState === "submitting" ? "Creating..." : "Create Agent Run"}
            </Button>
          </div>
        </div>
      </Card>
    </form>
  );
}
