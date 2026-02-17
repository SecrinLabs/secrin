"use client";

import { useState, useCallback } from "react";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CONTENT } from "@/constants/content";

type StepStatus = "pending" | "active" | "done" | "error";

type Step = {
  key: string;
  label: string;
  status: StepStatus;
};

const INITIAL_STEPS: Step[] = CONTENT.generateForm.steps.map((s) => ({
  ...s,
  status: "pending" as const,
}));

// Map current_step values from the backend to step indices
const STEP_INDEX: Record<string, number> = Object.fromEntries(
  CONTENT.generateForm.steps.map((s, i) => [s.key, i])
);
STEP_INDEX["complete"] = CONTENT.generateForm.steps.length;

const T = CONTENT.generateForm;

export function GenerateForm() {
  const [repoUrl, setRepoUrl] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [steps, setSteps] = useState<Step[]>(INITIAL_STEPS);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [result, setResult] = useState<{
    files_count?: number;
    total_time?: number;
    file_names?: string[];
  } | null>(null);

  const isRunning = jobId !== null && !isDone && !error;

  const updateSteps = (currentStep: string | null) => {
    setSteps((prev) => {
      const idx = currentStep ? (STEP_INDEX[currentStep] ?? -1) : -1;
      return prev.map((s, i) => ({
        ...s,
        status: i < idx ? "done" : i === idx ? "active" : s.status === "done" ? "done" : "pending",
      }));
    });
  };

  const pollStatus = useCallback(async (id: string) => {
    const poll = async () => {
      try {
        const res = await fetch(`/api/generate/${id}/status`);
        if (!res.ok) {
          setError(T.statusError);
          return;
        }

        const data = await res.json();
        updateSteps(data.current_step);

        if (data.status === "success") {
          setSteps((prev) => prev.map((s) => ({ ...s, status: "done" as const })));
          setIsDone(true);
          setResult(data.result);
          return;
        }

        if (data.status === "failed") {
          setError(data.error || T.errorFallback);
          setSteps((prev) =>
            prev.map((s) =>
              s.status === "active" ? { ...s, status: "error" as const } : s
            )
          );
          return;
        }

        setTimeout(poll, 3000);
      } catch {
        setError(T.serverLostError);
      }
    };

    poll();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);
    setIsDone(false);
    setResult(null);
    setSteps(INITIAL_STEPS.map((s) => ({ ...s, status: "pending" as const })));

    const trimmed = repoUrl.trim();
    if (!trimmed) return;

    setIsSubmitting(true);

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: trimmed }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(body?.error || T.errorFallback);
        return;
      }

      const data = await res.json();
      setJobId(data.job_id);
      setSteps((prev) => {
        const next = [...prev];
        next[0] = { ...next[0], status: "active" };
        return next;
      });
      pollStatus(data.job_id);
    } catch {
      setError(T.connectionError);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setJobId(null);
    setIsDone(false);
    setError(null);
    setResult(null);
    setSteps(INITIAL_STEPS.map((s) => ({ ...s, status: "pending" as const })));
    setRepoUrl("");
  };

  return (
    <div className="w-full space-y-6">
      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <Input
          type="text"
          placeholder={T.placeholder}
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          disabled={isRunning || isSubmitting}
          className="flex-1 h-11 text-base"
        />
        <Button
          type="submit"
          disabled={isRunning || isSubmitting || !repoUrl.trim()}
          size="lg"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            T.submitLabel
          )}
        </Button>
      </form>

      {/* Progress panel */}
      {(isRunning || isDone || error) && (
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <div className="space-y-3">
            {steps.map((step) => (
              <div key={step.key} className="flex items-center gap-3 text-sm">
                {step.status === "done" && (
                  <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                )}
                {step.status === "active" && (
                  <Loader2 className="h-4 w-4 animate-spin text-primary shrink-0" />
                )}
                {step.status === "pending" && (
                  <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/20 shrink-0" />
                )}
                {step.status === "error" && (
                  <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
                )}
                <span
                  className={
                    step.status === "pending"
                      ? "text-muted-foreground"
                      : step.status === "error"
                        ? "text-destructive"
                        : "text-foreground"
                  }
                >
                  {step.label}
                </span>
              </div>
            ))}
          </div>

          {/* Error */}
          {error && (
            <div className="pt-3 border-t border-border">
              <p className="text-sm text-destructive">{error}</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={handleReset}
              >
                {T.tryAgain}
              </Button>
            </div>
          )}

          {/* Success result */}
          {isDone && result && (
            <div className="pt-4 border-t border-border space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                <span className="font-medium text-green-600 dark:text-green-400">
                  {T.successMessage}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                {result.files_count} files generated in {result.total_time}s
              </div>

              {/* File list */}
              {result.file_names && result.file_names.length > 0 && (
                <div className="rounded-lg border border-border bg-muted/30 p-4 max-h-64 overflow-y-auto">
                  <div className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                    {T.generatedFiles}
                  </div>
                  <ul className="space-y-1">
                    {result.file_names.map((name) => (
                      <li
                        key={name}
                        className="flex items-center gap-2 text-sm text-foreground"
                      >
                        <FileText className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        {name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
              >
                {T.generateAnother}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
