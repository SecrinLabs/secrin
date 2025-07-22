"use client";

import React, { useState } from "react";
import { Activity, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@workspace/ui/lib/utils";
import { Badge } from "@workspace/ui/components/badge";
import { Button } from "@workspace/ui/components/button";
import { useServiceStatus } from "@workspace/ui/hooks/services/useServiceStatus";

interface SimpleServiceStatusButtonProps {
  className?: string;
}

export const SimpleServiceStatusWidget: React.FC<SimpleServiceStatusButtonProps> =
  React.memo(({ className }) => {
    const { data, isLoading, error } = useServiceStatus(true);

    if (isLoading || error) {
      return null;
    }

    const totalRunning = data?.summary?.total_running || 0;
    const hasRunningServices = data?.is_any_running || false;

    const getStatusIcon = () => {
      if (hasRunningServices) {
        return <Activity className="w-4 h-4 text-green-500 animate-pulse" />;
      }
      return <CheckCircle className="w-4 h-4 text-gray-400" />;
    };

    const getStatusText = () => {
      if (hasRunningServices) {
        return `${totalRunning} running`;
      }
      return "All idle";
    };

    return (
      <Button
        variant={hasRunningServices ? "default" : "secondary"}
        size="sm"
        className={cn(
          "fixed bottom-6 right-6 z-50 shadow-lg",
          hasRunningServices && "bg-green-500 hover:bg-green-600 text-white",
          className,
        )}
        onClick={() => {
          console.log("Service status:", data);
        }}
      >
        {getStatusIcon()}
        <span className="font-medium">{getStatusText()}</span>
        {hasRunningServices && (
          <Badge variant="secondary" className="ml-2 bg-white/20 text-white">
            {totalRunning}
          </Badge>
        )}
      </Button>
    );
  });

export default SimpleServiceStatusWidget;
