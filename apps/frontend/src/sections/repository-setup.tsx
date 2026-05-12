import { Badge, Button, Card, Field, SectionHeading, StatusLine } from "@patch/ui";
import { useQueryClient } from "@tanstack/react-query";
import { FolderGit, GitBranch, ShieldCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import { apiEndpoints, patchApi } from "../lib/api";
import { repositoryLabel, type SetActiveProps, useRepositories } from "../wireframe-data";

type SubmitState = "idle" | "submitting" | "success" | "error";

export function RepositorySetup({ setActive }: SetActiveProps) {
  const queryClient = useQueryClient();
  const { data: repositories = [], isLoading, isError } = useRepositories();
  const [owner, setOwner] = useState("");
  const [name, setName] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!owner.trim() || !name.trim()) {
      setSubmitState("error");
      return;
    }

    setSubmitState("submitting");

    try {
      await patchApi.createRepository({ owner: owner.trim(), name: name.trim() });
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.repositories] });
      setSubmitState("success");
      setActive("task");
    } catch {
      setSubmitState("error");
    }
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);

    try {
      await patchApi.deleteRepository(id);
      void queryClient.invalidateQueries({ queryKey: ["patch", apiEndpoints.repositories] });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <form className="grid gap-5 xl:grid-cols-[1fr_360px]" onSubmit={handleSubmit}>
      <Card className="p-5 md:p-6">
        <SectionHeading title="Connection" action={<Badge>{apiEndpoints.repositories}</Badge>} />
        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <Field
            label="GitHub Owner"
            name="owner"
            placeholder="user"
            value={owner}
            onChange={(event) => setOwner(event.target.value)}
            icon={<GitBranch size={16} />}
            required
          />
          <Field
            label="GitHub Repo"
            name="name"
            placeholder="repository-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            icon={<FolderGit size={16} />}
            required
          />
        </div>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-[var(--patch-muted)]">
            Request body: <span className="font-mono text-[var(--patch-ink)]">{"{ owner, name }"}</span>
          </p>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setActive("dashboard")}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitState === "submitting"}>
              <FolderGit size={15} />
              {submitState === "submitting" ? "Saving..." : "Save Repository"}
            </Button>
          </div>
        </div>
        {submitState === "error" && (
          <p className="mt-4 rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] px-4 py-3 text-sm text-[var(--patch-ink)]">
            Repository gagal disimpan. Pastikan owner dan name sesuai kontrak Stream 2.
          </p>
        )}
      </Card>

      <Card surface="dark" className="p-5">
        <div className="flex items-center gap-2 text-base font-semibold">
          <ShieldCheck size={18} />
          Contract Safety
        </div>
        <p className="mt-3 text-sm leading-6 text-[var(--patch-on-dark-muted)]">
          Frontend mengirim cookie auth otomatis dan hanya memakai endpoint repository dari Stream 2.
        </p>
        <div className="mt-6 space-y-3">
          <StatusLine label="List" value="GET /repositories" tone="dark" />
          <StatusLine label="Create" value="POST /repositories" tone="dark" />
          <StatusLine label="Delete" value="DELETE /repositories/{id}" tone="dark" />
        </div>
        <div className="mt-6 space-y-3">
          <div className="text-sm font-semibold text-white">Connected repositories</div>
          {isLoading && <p className="text-sm text-[var(--patch-on-dark-muted)]">Loading repositories...</p>}
          {isError && <p className="text-sm text-white">Unable to load repositories.</p>}
          {!isLoading && !isError && repositories.length === 0 && (
            <p className="text-sm text-[var(--patch-on-dark-muted)]">No connected repositories yet.</p>
          )}
          {repositories.map((repository) => (
            <div
              key={repository.id}
              className="rounded-[18px] border border-[var(--patch-dark-border)] bg-[var(--patch-on-dark-panel)] p-3"
            >
              <div className="truncate text-sm font-semibold text-white">{repositoryLabel(repository)}</div>
              <div className="mt-1 text-xs text-[var(--patch-on-dark-muted)]">{repository.default_branch}</div>
              <Button
                className="mt-3 w-full"
                variant="danger"
                disabled={deletingId === repository.id}
                onClick={() => void handleDelete(repository.id)}
              >
                {deletingId === repository.id ? "Disconnecting..." : "Disconnect"}
              </Button>
            </div>
          ))}
        </div>
      </Card>
    </form>
  );
}
