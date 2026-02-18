"use client";

import { useState, useCallback } from "react";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  FileText,
  BookOpen,
  Circle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CONTENT } from "@/constants/content";
import { cn } from "@/lib/utils";

const DOCS_URL = process.env.NEXT_PUBLIC_DOCS_URL || "http://localhost:3001";

type StepStatus = "pending" | "active" | "done" | "error";

type Step = {
  key: string;
  label: string;
  hasSubsteps?: boolean;
  substepTotal?: number;
  status: StepStatus;
};

interface SubstepInfo {
  substep: number | null;
  substep_total: number | null;
  substep_message: string | null;
}

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
  const [progress, setProgress] = useState(0);
  const [activeSubstep, setActiveSubstep] = useState<SubstepInfo>({
    substep: null,
    substep_total: null,
    substep_message: null,
  });
  const [activeStepKey, setActiveStepKey] = useState<string | null>(null);
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
        setProgress(data.progress ?? 0);
        setActiveStepKey(data.current_step ?? null);

        // Update substep info
        setActiveSubstep({
          substep: data.substep ?? null,
          substep_total: data.substep_total ?? null,
          substep_message: data.substep_message ?? null,
        });

        if (data.status === "success") {
          setSteps((prev) => prev.map((s) => ({ ...s, status: "done" as const })));
          setIsDone(true);
          setProgress(100);
          setResult(data.result);
          setActiveSubstep({ substep: null, substep_total: null, substep_message: null });
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

        setTimeout(poll, 2000);
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
    setProgress(0);
    setActiveSubstep({ substep: null, substep_total: null, substep_message: null });
    setActiveStepKey(null);
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
    setProgress(0);
    setActiveSubstep({ substep: null, substep_total: null, substep_message: null });
    setActiveStepKey(null);
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
          {/* Overall progress bar */}
          {(isRunning || isDone) && (
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <div className="flex-1 h-2.5 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-700 ease-out",
                    isDone ? "bg-green-500" : progress > 0 ? "bg-blue-500" : "bg-blue-500/30 animate-pulse"
                  )}
                  style={{ width: `${Math.max(progress, isDone ? 100 : 2)}%` }}
                />
              </div>
              <span className="tabular-nums font-medium w-10 text-right">
                {isDone ? 100 : progress}%
              </span>
            </div>
          )}

          {/* Step list */}
          <div className="space-y-1">
            {steps.map((step) => {
              const isActive = step.status === "active";
              const showSubstep =
                isActive &&
                step.key === activeStepKey &&
                step.hasSubsteps &&
                activeSubstep.substep != null &&
                activeSubstep.substep > 0;

              return (
                <div key={step.key}>
                  {/* Step row */}
                  <div
                    className={cn(
                      "flex items-center gap-3 text-sm py-1 transition-colors duration-300",
                      step.status === "done" && "text-green-600 dark:text-green-400",
                      step.status === "active" && "text-blue-600 dark:text-blue-400 font-medium",
                      step.status === "pending" && "text-muted-foreground/50",
                      step.status === "error" && "text-destructive"
                    )}
                  >
                    {step.status === "done" && (
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                    )}
                    {step.status === "active" && (
                      <Loader2 className="h-4 w-4 animate-spin shrink-0" />
                    )}
                    {step.status === "pending" && (
                      <Circle className="h-4 w-4 shrink-0 opacity-30" />
                    )}
                    {step.status === "error" && (
                      <AlertCircle className="h-4 w-4 shrink-0" />
                    )}
                    <span className="flex-1">{step.label}</span>

                    {/* Substep fraction on the active step line */}
                    {showSubstep && (
                      <span className="tabular-nums text-xs text-muted-foreground">
                        {activeSubstep.substep}/{activeSubstep.substep_total}
                      </span>
                    )}
                  </div>

                  {/* Substep detail line */}
                  {showSubstep && (
                    <div className="flex items-center gap-2 pl-7 py-0.5 animate-in fade-in duration-200">
                      <span className="text-blue-400/60 text-xs">└</span>
                      <span className="text-xs text-muted-foreground truncate flex-1">
                        {activeSubstep.substep_message ||
                          `Substep ${activeSubstep.substep} of ${activeSubstep.substep_total}`}
                      </span>
                      {/* Mini substep progress bar */}
                      <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden shrink-0">
                        <div
                          className="h-full bg-blue-400 rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.round(
                              ((activeSubstep.substep ?? 0) / (activeSubstep.substep_total ?? 1)) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
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
            <div className="pt-4 border-t border-border space-y-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500" />
                <span className="font-medium text-green-600 dark:text-green-400">
                  {T.successMessage}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                {result.files_count} files generated in {result.total_time}s
              </div>

              {/* View Documentation button */}
              <a
                href={DOCS_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="block animate-in fade-in slide-in-from-bottom-2 duration-500"
              >
                <Button variant="default" className="w-full gap-2">
                  <BookOpen className="h-4 w-4" />
                  View Documentation
                </Button>
              </a>

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
