"use client";

import React, { useState } from "react";
import {
  Activity,
  CheckCircle,
  Loader2,
  AlertCircle,
  X,
  Wifi,
  WifiOff,
  RefreshCw,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@workspace/ui/lib/utils";
import { Badge } from "@workspace/ui/components/badge";
import { Button } from "@workspace/ui/components/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@workspace/ui/components/dialog";
import {
  useServiceStatusWidget,
  type Service,
  type ServicesData,
} from "@workspace/ui/hooks/services/useServiceStatus";

// Service Status Button Component
interface ServiceStatusButtonProps {
  isRunning: boolean;
  totalRunning: number;
  isConnected?: boolean;
  onClick: () => void;
  className?: string;
}

const ServiceStatusButton: React.FC<ServiceStatusButtonProps> = ({
  isRunning,
  totalRunning,
  isConnected = true,
  onClick,
  className,
}) => {
  const getStatusIcon = () => {
    if (!isConnected) {
      return <AlertCircle className="w-4 h-4 text-orange-500" />;
    }

    if (isRunning) {
      return <Activity className="w-4 h-4 text-green-500 animate-pulse" />;
    }

    return <CheckCircle className="w-4 h-4 text-gray-400" />;
  };

  const getStatusText = () => {
    if (!isConnected) {
      return "Disconnected";
    }

    if (isRunning) {
      return `${totalRunning} running`;
    }

    return "All idle";
  };

  const getButtonVariant = () => {
    if (!isConnected) return "outline";
    if (isRunning) return "default";
    return "secondary";
  };

  return (
    <Button
      variant={getButtonVariant()}
      size="sm"
      onClick={onClick}
      className={cn(
        "fixed bottom-6 right-6 z-50 shadow-lg transition-all duration-200",
        "hover:scale-105 focus:scale-105",
        isRunning &&
          isConnected &&
          "bg-green-500 hover:bg-green-600 text-white",
        !isConnected && "border-orange-500 text-orange-600",
        className
      )}
    >
      {getStatusIcon()}
      <span className="font-medium">{getStatusText()}</span>
      {isRunning && (
        <Badge variant="secondary" className="ml-2 bg-white/20 text-white">
          {totalRunning}
        </Badge>
      )}
    </Button>
  );
};

// Service Card Component
interface ServiceCardProps {
  service: Service;
  type: "scraper" | "embedder" | "other";
  onStop?: (serviceId: string) => void;
  className?: string;
}

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

const ServiceCard: React.FC<ServiceCardProps> = ({
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

// Service Status Modal Component
interface ServiceStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: ServicesData | null;
  isConnected: boolean;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

const ServiceStatusModal: React.FC<ServiceStatusModalProps> = ({
  isOpen,
  onClose,
  data,
  isConnected,
  isLoading = false,
  error,
  onRefresh,
}) => {
  const totalRunning = data?.summary?.total_running || 0;
  const allServices = data
    ? [
        ...data.services.scrapers,
        ...data.services.embedders,
        ...data.services.others,
      ]
    : [];

  const getServiceType = (serviceName: string) => {
    if (serviceName.startsWith("scraper")) return "scraper";
    if (serviceName === "embedder") return "embedder";
    return "other";
  };

  const renderConnectionStatus = () => (
    <div className="flex items-center gap-2 text-sm">
      {isConnected ? (
        <>
          <Wifi className="w-4 h-4 text-green-500" />
          <span className="text-green-600">Connected</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4 text-orange-500" />
          <span className="text-orange-600">Disconnected</span>
        </>
      )}
    </div>
  );

  const renderSummary = () => {
    if (!data) return null;

    const { scrapers_running, embedders_running, others_running } =
      data.summary;

    return (
      <div className="flex flex-wrap gap-2 mb-6">
        <Badge variant="outline" className="flex items-center gap-1">
          <span className="text-xs">🕷️</span>
          Scrapers: {scrapers_running}
        </Badge>
        <Badge variant="outline" className="flex items-center gap-1">
          <span className="text-xs">📄</span>
          Processors: {embedders_running}
        </Badge>
        {others_running > 0 && (
          <Badge variant="outline" className="flex items-center gap-1">
            <span className="text-xs">⚙️</span>
            Others: {others_running}
          </Badge>
        )}
      </div>
    );
  };

  const renderServices = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-600">Loading services...</span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center py-8">
          <div className="text-red-500 mb-2">❌ Error loading services</div>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          )}
        </div>
      );
    }

    if (!data || allServices.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-2">✨ All services are idle</div>
          <p className="text-sm text-gray-600">
            No background services are currently running
          </p>
        </div>
      );
    }

    return (
      <div className="grid gap-3">
        {allServices.map((service) => (
          <ServiceCard
            key={service.id}
            service={service}
            type={getServiceType(service.name)}
            onStop={(serviceId: string) => {
              console.log("Stop service:", serviceId);
              // TODO: Implement stop functionality
            }}
          />
        ))}
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              Background Services
              {totalRunning > 0 && (
                <Badge
                  variant="secondary"
                  className="bg-green-100 text-green-800"
                >
                  {totalRunning} running
                </Badge>
              )}
            </DialogTitle>
            <div className="flex items-center gap-2">
              {renderConnectionStatus()}
              {onRefresh && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onRefresh}
                  className="h-8 w-8 p-0"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-auto">
          {renderSummary()}
          {renderServices()}
        </div>

        <div className="flex-shrink-0 pt-4 border-t">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>
              {isConnected ? "Real-time updates" : "Polling every 5 seconds"}
            </span>
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Main Service Status Widget Component
interface ServiceStatusWidgetProps {
  className?: string;
}

export const ServiceStatusWidget: React.FC<ServiceStatusWidgetProps> =
  React.memo(({ className }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const {
      data,
      isLoading,
      isConnected,
      error,
      hasRunningServices,
      totalRunning,
    } = useServiceStatusWidget(isModalOpen);

    const handleOpenModal = React.useCallback(() => {
      setIsModalOpen(true);
    }, []);

    const handleCloseModal = React.useCallback(() => {
      setIsModalOpen(false);
    }, []);

    const handleRefresh = React.useCallback(() => {
      // The hook will automatically refetch data
      console.log("Refreshing service status...");
    }, []);

    return (
      <>
        <ServiceStatusButton
          isRunning={hasRunningServices}
          totalRunning={totalRunning}
          isConnected={isConnected}
          onClick={handleOpenModal}
          className={className}
        />

        <ServiceStatusModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          data={data || null}
          isConnected={isConnected}
          isLoading={isLoading}
          error={
            error
              ? error instanceof Error
                ? error.message
                : String(error)
              : null
          }
          onRefresh={handleRefresh}
        />
      </>
    );
  });

export default ServiceStatusWidget;
