import { Badge, Button, Card, Field, SectionHeading, StatusLine } from "@patch/ui";
import { FolderGit, GitBranch, ShieldCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import { apiEndpoints, patchApi } from "../api-contract";
import type { SetActiveProps } from "../wireframe-data";

type SubmitState = "idle" | "submitting" | "success" | "error";

export function RepositorySetup({ setActive }: SetActiveProps) {
  const [owner, setOwner] = useState("user");
  const [name, setName] = useState("fastapi-auth-app");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!owner.trim() || !name.trim()) {
      setSubmitState("error");
      return;
    }

    setSubmitState("submitting");

    try {
      await patchApi.createRepository({ owner: owner.trim(), name: name.trim() });
      setSubmitState("success");
      setActive("task");
    } catch {
      setSubmitState("error");
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
            placeholder="fastapi-auth-app"
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
      </Card>
    </form>
  );
}
