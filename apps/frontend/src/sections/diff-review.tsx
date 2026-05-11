import { Badge, Button, Card, FileRow, SectionHeading, Textarea } from "@patch/ui";
import { GitPullRequest, MessageSquarePlus } from "lucide-react";
import { type FormEvent, useState } from "react";
import { apiEndpoints, type FeedbackCreate, patchApi } from "../api-contract";
import { type SetActiveProps, useAgentRun, useAgentRunDiff } from "../wireframe-data";

type SubmitState = "idle" | "submitting" | "success" | "error";

export function DiffReview({ setActive }: SetActiveProps) {
  const { data: agentRun } = useAgentRun();
  const { data: diffFiles } = useAgentRunDiff(agentRun.id);
  const [instruction, setInstruction] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");

  const handleFeedbackSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const feedbackCreate: FeedbackCreate = {
      instruction: instruction.trim(),
    };

    if (!feedbackCreate.instruction) {
      setSubmitState("error");
      return;
    }

    setSubmitState("submitting");

    try {
      await patchApi.submitFeedback(agentRun.id, feedbackCreate);
      setSubmitState("success");
      setActive("run");
    } catch {
      setSubmitState("error");
    }
  };

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <Card className="p-5">
        <SectionHeading title="DiffFileRead[]" action={<Badge>{apiEndpoints.agentRunDiff(agentRun.id)}</Badge>} />
        <div className="mt-5 space-y-3">
          {diffFiles.map((file) => (
            <div key={file.file_path} className="space-y-3">
              <FileRow path={file.file_path} additions={`+${file.additions}`} deletions={`-${file.deletions}`} />
              {file.patch && (
                <pre className="max-h-48 overflow-auto rounded-[18px] bg-[var(--patch-ink)] p-4 text-xs leading-6 text-white">
                  {file.patch}
                </pre>
              )}
            </div>
          ))}
        </div>
      </Card>

      <form className="space-y-5" onSubmit={handleFeedbackSubmit}>
        <Card className="p-5">
          <SectionHeading title="FeedbackCreate" action={<Badge>POST</Badge>} />
          <Textarea
            name="instruction"
            className="mt-5 min-h-44 w-full rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm leading-6"
            value={instruction}
            onChange={(event) => setInstruction(event.target.value)}
            placeholder="Request follow-up changes for the same pull request branch"
          />
          {submitState === "error" && (
            <p className="mt-3 text-sm text-[var(--patch-ink)]">
              Feedback membutuhkan instruction dan parent run harus berstatus succeeded.
            </p>
          )}
          <Button className="mt-4 w-full" type="submit" disabled={submitState === "submitting"}>
            <MessageSquarePlus size={15} />
            {submitState === "submitting" ? "Submitting..." : "Submit Feedback"}
          </Button>
        </Card>

        <Card surface="dark" className="p-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-white">
            <GitPullRequest size={16} />
            Pull Request Lookup
          </div>
          <p className="mt-3 text-sm leading-6 text-[var(--patch-on-dark-muted)]">
            PR data tersedia lewat {apiEndpoints.agentRunPullRequest(agentRun.id)} dan follow-up membuka run child baru.
          </p>
        </Card>
      </form>
    </div>
  );
}
