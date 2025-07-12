"use client";

import React from "react";
import { Activity, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@workspace/ui/lib/utils";
import { Badge } from "@workspace/ui/components/badge";
import { Button } from "@workspace/ui/components/button";

interface ServiceStatusButtonProps {
  isRunning: boolean;
  totalRunning: number;
  isConnected?: boolean;
  onClick: () => void;
  className?: string;
}

export const ServiceStatusButton: React.FC<ServiceStatusButtonProps> = ({
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
