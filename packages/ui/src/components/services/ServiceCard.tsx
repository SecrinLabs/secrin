"use client";

import React from "react";
import { Loader2, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { cn } from "@workspace/ui/lib/utils";
import { Badge } from "@workspace/ui/components/badge";
import { Button } from "@workspace/ui/components/button";
import type { Service } from "@workspace/ui/hooks/services/useServiceStatus";

// Simple time formatting utility
const formatDuration = (start: Date, end?: Date) => {
  const endTime = end || new Date();
  const diffMs = endTime.getTime() - start.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) return `${diffDays}d ${diffHours % 24}h`;
  if (diffHours > 0) return `${diffHours}h ${diffMinutes % 60}m`;
  if (diffMinutes > 0) return `${diffMinutes}m ${diffSeconds % 60}s`;
  return `${diffSeconds}s`;
};

interface ServiceCardProps {
  service: Service;
  type: "scraper" | "embedder" | "other";
  onStop?: (serviceId: string) => void;
  className?: string;
}

export const ServiceCard: React.FC<ServiceCardProps> = ({
  service,
  type,
  onStop,
  className,
}) => {
  const getServiceIcon = () => {
    switch (type) {
      case "scraper":
        return "🕷️";
      case "embedder":
        return "📄";
      default:
        return "⚙️";
    }
  };

  const getStatusIcon = () => {
    switch (service.status) {
      case "running":
        return <Loader2 className="w-4 h-4 text-green-500 animate-spin" />;
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-blue-500" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = () => {
    switch (service.status) {
      case "running":
        return (
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            Running
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="secondary" className="bg-blue-100 text-blue-800">
            Completed
          </Badge>
        );
      case "error":
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const formatServiceName = (name: string) => {
    return name
      .replace(/^scraper-?/i, "")
      .replace(/embedder/i, "Document Processor")
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const getDuration = () => {
    try {
      const startTime = new Date(service.started_at);
      const endTime = service.completed_at
        ? new Date(service.completed_at)
        : new Date();

      if (service.status === "running") {
        return `Running for ${formatDuration(startTime)}`;
      } else {
        return `Completed in ${formatDuration(startTime, endTime)}`;
      }
    } catch (error) {
      return "Duration unknown";
    }
  };

  return (
    <div
      className={cn(
        "border rounded-lg p-4 transition-all duration-200",
        "hover:shadow-md hover:border-gray-300",
        service.status === "running" && "border-green-200 bg-green-50/50",
        service.status === "completed" && "border-blue-200 bg-blue-50/50",
        service.status === "error" && "border-red-200 bg-red-50/50",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-2xl">{getServiceIcon()}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {getStatusIcon()}
              <h3 className="font-medium text-sm truncate">
                {formatServiceName(service.name)}
              </h3>
              {getStatusBadge()}
            </div>

            {service.description && (
              <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                {service.description}
              </p>
            )}

            <p className="text-xs text-gray-500">{getDuration()}</p>
          </div>
        </div>

        {service.status === "running" && onStop && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onStop(service.id)}
            className="ml-2 text-xs"
          >
            Stop
          </Button>
        )}
      </div>
    </div>
  );
};
