"use client";

import React from "react";
import { X, Wifi, WifiOff, RefreshCw } from "lucide-react";
import { cn } from "@workspace/ui/lib/utils";
import { Button } from "@workspace/ui/components/button";
import { Badge } from "@workspace/ui/components/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from "@workspace/ui/components/dialog";
import { ServiceCard } from "@workspace/ui/components/services/ServiceCard";
import type { ServicesData } from "@workspace/ui/hooks/services/useServiceStatus";

interface ServiceStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: ServicesData | null;
  isConnected: boolean;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

export const ServiceStatusModal: React.FC<ServiceStatusModalProps> = ({
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
