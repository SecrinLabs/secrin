"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from "lucide-react";
import { DocGenStatus } from "@/types/project";
import { cn } from "@/lib/utils";

interface JobProgress {
  status: string;
  progress: number;
  current_step: string | null;
  error: string | null;
}

interface DocGenStatusBadgeProps {
  status?: DocGenStatus | null;
  lastDocGenAt?: string | null;
  projectId?: string;
  className?: string;
}

const statusConfig: Record<
  DocGenStatus,
  { icon: typeof CheckCircle; label: string; className: string }
> = {
  pending: {
    icon: Clock,
    label: "Pending",
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
  className,
}: DocGenStatusBadgeProps) {
  const [jobProgress, setJobProgress] = useState<JobProgress | null>(null);
  const [currentStatus, setCurrentStatus] = useState(status);

  const pollStatus = useCallback(async () => {
    if (!projectId) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/regenerate/status`);
      if (!res.ok) return;
      const data: JobProgress = await res.json();
      setJobProgress(data);

      if (data.status === "success" || data.status === "failed") {
        setCurrentStatus(data.status as DocGenStatus);
      }
    } catch {
      // Silently ignore polling errors
    }
  }, [projectId]);

  useEffect(() => {
    setCurrentStatus(status);
  }, [status]);

  useEffect(() => {
    if (currentStatus !== "running" || !projectId) {
      setJobProgress(null);
      return;
    }

    // Start polling
    pollStatus();
    const interval = setInterval(pollStatus, 3000);
    return () => clearInterval(interval);
  }, [currentStatus, projectId, pollStatus]);

  if (!currentStatus) {
    return null;
  }

  const config = statusConfig[currentStatus];
  const Icon = config.icon;
  const isAnimated = currentStatus === "running";

  return (
    <div className="space-y-1">
      <div
        className={cn(
          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
          config.className,
          className
        )}
      >
        <Icon className={cn("h-3.5 w-3.5", isAnimated && "animate-spin")} />
        <span>{config.label}</span>
        {lastDocGenAt && currentStatus === "success" && (
          <span className="text-muted-foreground ml-1">
            · {formatRelativeTime(lastDocGenAt)}
          </span>
        )}
      </div>

      {/* Progress details when running */}
      {currentStatus === "running" && jobProgress && jobProgress.progress > 0 && (
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all duration-500"
                style={{ width: `${jobProgress.progress}%` }}
              />
            </div>
            <span className="tabular-nums">{jobProgress.progress}%</span>
          </div>
          {jobProgress.current_step && (
            <p className="text-xs text-muted-foreground truncate">
              {jobProgress.current_step}
            </p>
          )}
        </div>
      )}

      {/* Error message */}
      {currentStatus === "failed" && jobProgress?.error && (
        <p className="text-xs text-red-500 truncate max-w-xs">
          {jobProgress.error}
        </p>
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

      <div className="flex items-center gap-3">
        <DocGenStatusBadge
          status={docGenStatus}
          lastDocGenAt={lastDocGenAt}
          projectId={projectId}
        />

        {onTriggerRegenerate && docGenStatus !== "running" && (
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
