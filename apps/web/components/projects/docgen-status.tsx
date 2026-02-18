"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  BookOpen,
  Circle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DocGenStatus } from "@/types/project";
import { cn } from "@/lib/utils";

const DOCS_URL =
  process.env.NEXT_PUBLIC_DOCS_URL || "http://localhost:3001";

interface JobProgress {
  status: string;
  progress: number;
  current_step: string | null;
  step_number: number | null;
  total_steps: number | null;
  substep: number | null;
  substep_total: number | null;
  substep_message: string | null;
  error: string | null;
}

/**
 * The 8 pipeline steps — must match backend total_steps = 8.
 * hasSubsteps indicates the step reports granular sub-progress.
 */
const PIPELINE_STEPS = [
  { step: 1, label: "Analyzing codebase" },
  { step: 2, label: "Generating Arc42 documentation", hasSubsteps: true, substepTotal: 12 },
  { step: 3, label: "Generating C4 diagrams", hasSubsteps: true, substepTotal: 4 },
  { step: 4, label: "Generating Diataxis documentation", hasSubsteps: true, substepTotal: 4 },
  { step: 5, label: "Adding provenance and citations" },
  { step: 6, label: "Generating index and navigation" },
  { step: 7, label: "Committing to GitHub" },
  { step: 8, label: "Writing local docs" },
];

interface DocGenStatusBadgeProps {
  status?: DocGenStatus | null;
  lastDocGenAt?: string | null;
  projectId?: string;
  projectSlug?: string;
  className?: string;
}

const statusConfig: Record<
  DocGenStatus,
  { icon: typeof CheckCircle; label: string; className: string }
> = {
  pending: {
    icon: Clock,
    label: "Queued",
    className: "text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30",
  },
  running: {
    icon: Loader2,
    label: "Generating...",
    className: "text-blue-600 bg-blue-100 dark:bg-blue-900/30",
  },
  success: {
    icon: CheckCircle,
    label: "Up to date",
    className: "text-green-600 bg-green-100 dark:bg-green-900/30",
  },
  failed: {
    icon: XCircle,
    label: "Failed",
    className: "text-red-600 bg-red-100 dark:bg-red-900/30",
  },
};

export function DocGenStatusBadge({
  status,
  lastDocGenAt,
  projectId,
  projectSlug,
  className,
}: DocGenStatusBadgeProps) {
  const [jobProgress, setJobProgress] = useState<JobProgress | null>(null);
  const [currentStatus, setCurrentStatus] = useState(status);
  const [showSuccess, setShowSuccess] = useState(status === "success");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ---- Polling callback ----
  const pollStatus = useCallback(async () => {
    if (!projectId) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/regenerate/status`);
      if (!res.ok) return;
      const data: JobProgress = await res.json();
      setJobProgress(data);

      // Reflect status transitions reported by the backend
      if (data.status === "running") {
        setCurrentStatus("running");
      } else if (data.status === "success") {
        setCurrentStatus("success");
        setShowSuccess(true);
      } else if (data.status === "failed") {
        setCurrentStatus("failed");
      }
    } catch {
      // Silently ignore polling errors
    }
  }, [projectId]);

  // ---- Sync prop → local state ----
  useEffect(() => {
    setCurrentStatus(status);
    if (status === "success") setShowSuccess(true);
  }, [status]);

  // ---- Start / stop polling ----
  // Poll when status is "pending" OR "running" so we catch every transition.
  useEffect(() => {
    const shouldPoll =
      (currentStatus === "pending" || currentStatus === "running") && !!projectId;

    if (!shouldPoll) {
      // Not in an active generation state — clear any existing interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (currentStatus !== "pending" && currentStatus !== "running") {
        // Keep jobProgress around briefly for the success/failed UI,
        // but don't null it immediately so the step list stays visible
        // during the success animation.
      }
      return;
    }

    // Kick off an immediate poll, then every 2 s
    pollStatus();
    intervalRef.current = setInterval(pollStatus, 2000);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [currentStatus, projectId, pollStatus]);

  if (!currentStatus) {
    return null;
  }

  const config = statusConfig[currentStatus];
  const Icon = config.icon;
  const isActive = currentStatus === "running" || currentStatus === "pending";
  const isRunning = currentStatus === "running";
  const stepNumber = jobProgress?.step_number ?? 0;
  const progressPct = jobProgress?.progress ?? 0;

  return (
    <div className="space-y-2 w-full">
      {/* ---- Status badge ---- */}
      <div
        className={cn(
          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
          config.className,
          className
        )}
      >
        <Icon
          className={cn(
            "h-3.5 w-3.5",
            (isRunning || currentStatus === "pending") && "animate-spin"
          )}
        />
        <span>{config.label}</span>
        {lastDocGenAt && currentStatus === "success" && (
          <span className="text-muted-foreground ml-1">
            · {formatRelativeTime(lastDocGenAt)}
          </span>
        )}
      </div>

      {/* ---- Rich progress panel (visible throughout generation) ---- */}
      {isActive && (
        <div className="space-y-3 rounded-lg border bg-card p-3 animate-in fade-in duration-300">
          {/* Overall progress bar */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-700 ease-out",
                  progressPct > 0 ? "bg-blue-500" : "bg-blue-500/30 animate-pulse"
                )}
                style={{ width: `${Math.max(progressPct, 2)}%` }}
              />
            </div>
            <span className="tabular-nums font-medium w-8 text-right">
              {progressPct}%
            </span>
          </div>

          {/* Queued message (before worker picks up the job) */}
          {currentStatus === "pending" && !jobProgress?.step_number && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="h-3.5 w-3.5 animate-pulse" />
              <span>Queued — waiting for worker to pick up job...</span>
            </div>
          )}

          {/* Step list — always visible once we have any progress data or are running */}
          {(isRunning || (jobProgress && jobProgress.step_number)) && (
            <div className="space-y-0.5">
              {PIPELINE_STEPS.map(({ step, label, hasSubsteps }) => {
                const isCompleted = stepNumber > step;
                const isStepActive = stepNumber === step;
                const isPending = stepNumber < step;

                return (
                  <div key={step}>
                    {/* Step row */}
                    <div
                      className={cn(
                        "flex items-center gap-2 text-xs py-0.5 transition-colors duration-300",
                        isCompleted && "text-green-600 dark:text-green-400",
                        isStepActive && "text-blue-600 dark:text-blue-400 font-medium",
                        isPending && "text-muted-foreground/40"
                      )}
                    >
                      {isCompleted && (
                        <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                      )}
                      {isStepActive && (
                        <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" />
                      )}
                      {isPending && (
                        <Circle className="h-3.5 w-3.5 shrink-0 opacity-40" />
                      )}
                      <span>{label}</span>
                      {/* Show substep fraction on the active step line */}
                      {isStepActive && hasSubsteps && jobProgress?.substep != null && jobProgress.substep > 0 && (
                        <span className="ml-auto tabular-nums text-[11px] text-muted-foreground">
                          {jobProgress.substep}/{jobProgress.substep_total}
                        </span>
                      )}
                    </div>

                    {/* Substep detail line */}
                    {isStepActive &&
                      hasSubsteps &&
                      jobProgress?.substep != null &&
                      jobProgress.substep_total != null &&
                      jobProgress.substep > 0 && (
                        <div className="flex items-center gap-1.5 pl-[22px] py-0.5">
                          <span className="text-blue-400/60 text-[11px]">└</span>
                          <span className="text-[11px] text-muted-foreground truncate">
                            {jobProgress.substep_message ||
                              `Substep ${jobProgress.substep} of ${jobProgress.substep_total}`}
                          </span>
                          {/* Mini substep progress bar */}
                          <div className="ml-auto flex items-center gap-1.5 shrink-0">
                            <div className="w-16 h-1 bg-muted rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-400 rounded-full transition-all duration-500"
                                style={{
                                  width: `${Math.round(
                                    (jobProgress.substep / jobProgress.substep_total) * 100
                                  )}%`,
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Current step text fallback (when step_number isn't available yet but current_step is) */}
          {!jobProgress?.step_number && jobProgress?.current_step && (
            <p className="text-xs text-muted-foreground truncate">
              {jobProgress.current_step}
            </p>
          )}
        </div>
      )}

      {/* ---- Completed: all-green step list ---- */}
      {currentStatus === "success" && jobProgress?.step_number && (
        <div className="space-y-3 rounded-lg border border-green-200 dark:border-green-900/40 bg-green-50/50 dark:bg-green-950/20 p-3 animate-in fade-in duration-500">
          <div className="flex items-center gap-2 text-xs font-medium text-green-600 dark:text-green-400">
            <CheckCircle className="h-4 w-4" />
            <span>Generation complete</span>
            {jobProgress?.progress != null && (
              <span className="ml-auto text-muted-foreground font-normal">
                {(jobProgress as any)?.result?.files_count
                  ? `${(jobProgress as any).result.files_count} files`
                  : ""}
              </span>
            )}
          </div>
          <div className="space-y-0.5">
            {PIPELINE_STEPS.map(({ step, label }) => (
              <div
                key={step}
                className="flex items-center gap-2 text-xs py-0.5 text-green-600 dark:text-green-400"
              >
                <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---- Error message ---- */}
      {currentStatus === "failed" && jobProgress?.error && (
        <div className="rounded-lg border border-red-200 dark:border-red-900/40 bg-red-50/50 dark:bg-red-950/20 p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-red-600 dark:text-red-400 mb-1">
            <XCircle className="h-4 w-4 shrink-0" />
            <span>Generation failed</span>
          </div>
          <p className="text-xs text-red-500 dark:text-red-400/80 break-words">
            {jobProgress.error}
          </p>
        </div>
      )}

      {/* ---- View Documentation button on success ---- */}
      {showSuccess && currentStatus === "success" && projectSlug && (
        <a
          href={`${DOCS_URL}/${projectSlug}`}
          target="_blank"
          rel="noopener noreferrer"
          className="block animate-in fade-in slide-in-from-bottom-2 duration-500"
        >
          <Button variant="default" size="sm" className="w-full gap-2">
            <BookOpen className="h-4 w-4" />
            View Documentation
          </Button>
        </a>
      )}
    </div>
  );
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

interface SourceRepoInfoProps {
  sourceRepoUrl?: string;
  sourceRepoOwner?: string;
  sourceRepoName?: string;
  sourceRepoBranch?: string;
  docGenStatus?: DocGenStatus | null;
  lastDocGenAt?: string | null;
  projectId?: string;
  projectSlug?: string;
  onTriggerRegenerate?: () => void;
  isRegenerating?: boolean;
}

export function SourceRepoInfo({
  sourceRepoUrl,
  sourceRepoOwner,
  sourceRepoName,
  sourceRepoBranch,
  docGenStatus,
  lastDocGenAt,
  projectId,
  projectSlug,
  onTriggerRegenerate,
  isRegenerating,
}: SourceRepoInfoProps) {
  if (!sourceRepoUrl) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">Source:</span>
        <a
          href={sourceRepoUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-primary hover:underline"
        >
          {sourceRepoOwner}/{sourceRepoName}
        </a>
        {sourceRepoBranch && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
            {sourceRepoBranch}
          </span>
        )}
      </div>

      <div className="space-y-2">
        <DocGenStatusBadge
          status={docGenStatus}
          lastDocGenAt={lastDocGenAt}
          projectId={projectId}
          projectSlug={projectSlug}
        />

        {onTriggerRegenerate && docGenStatus !== "running" && docGenStatus !== "pending" && (
          <button
            onClick={onTriggerRegenerate}
            disabled={isRegenerating}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn("h-3 w-3", isRegenerating && "animate-spin")} />
            Regenerate
          </button>
        )}
      </div>
    </div>
  );
}
