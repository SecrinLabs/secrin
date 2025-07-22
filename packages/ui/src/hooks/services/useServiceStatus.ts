import { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import { endpoints } from "@workspace/ui/lib/config";

// Types for service status
export interface Service {
  id: string;
  name: string;
  description: string;
  started_at: string;
  status: "running" | "completed" | "error";
  completed_at?: string;
}

export interface ServicesSummary {
  total_running: number;
  scrapers_running: number;
  embedders_running: number;
  others_running: number;
}

export interface ServicesData {
  services: {
    scrapers: Service[];
    embedders: Service[];
    others: Service[];
  };
  summary: ServicesSummary;
  websocket?: {
    active_connections: number;
    connection_details: any[];
  };
  is_any_running: boolean;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  timestamp: string;
  service?: Service;
  services?: ServicesData["services"];
  summary?: ServicesSummary;
  is_any_running?: boolean;
  message?: string;
  notification_type?: "info" | "success" | "warning" | "error";
}

// Fetch service status via REST API
const fetchServiceStatus = async (): Promise<ServicesData> => {
  const response = await fetch(endpoints.status);

  if (!response.ok) {
    throw new Error(`Failed to fetch service status: ${response.statusText}`);
  }

  return response.json();
};

// Hook for basic service status (polling-based)
export const useServiceStatus = (enabled: boolean = true) => {
  const query = useQuery({
    queryKey: ["service-status"],
    queryFn: fetchServiceStatus,
    refetchInterval: enabled ? 5000 : false, // Poll every 5 seconds when enabled
    staleTime: 2000,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Handle errors manually
  useEffect(() => {
    if (query.error) {
      console.error("Error fetching service status:", query.error);
      toast.error("Failed to fetch service status");
    }
  }, [query.error]);

  return query;
};

// Hook for real-time WebSocket connection
export const useServiceWebSocket = (
  endpoint: "status" | "notifications" | "live"
) => {
  const [data, setData] = useState<ServicesData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connect = useCallback(() => {
    // Don't create a new connection if one already exists
    if (ws && ws.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = endpoints.websocket(endpoint);
      const websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log(`Connected to WebSocket: ${endpoint}`);
      };

      websocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          // Handle different message types
          if (
            message.type === "status_update" ||
            message.type === "live_update"
          ) {
            setData({
              services: message.services!,
              summary: message.summary!,
              is_any_running: message.is_any_running || false,
            });
          } else if (message.type === "service_started") {
            toast.success(`${message.service?.name} started`, {
              description: message.service?.description,
            });
          } else if (message.type === "service_completed") {
            toast.info(`${message.service?.name} completed`, {
              description: `Finished in ${getServiceDuration(message.service)}`,
            });
          } else if (message.type === "service_error") {
            toast.error(`${message.service?.name} failed`, {
              description: message.message,
            });
          } else if (message.type === "custom_notification") {
            const toastFn = {
              info: toast.info,
              success: toast.success,
              warning: toast.warning,
              error: toast.error,
            }[message.notification_type || "info"];

            toastFn(message.message || "Service notification");
          }
        } catch (parseError) {
          console.error("Error parsing WebSocket message:", parseError);
        }
      };

      websocket.onclose = (event) => {
        setIsConnected(false);

        if (!event.wasClean) {
          setError("Connection lost unexpectedly");
          console.warn("WebSocket closed unexpectedly:", event);

          // Attempt to reconnect after 3 seconds
          setTimeout(() => {
            if (ws === websocket) {
              connect();
            }
          }, 3000);
        }
      };

      websocket.onerror = (error) => {
        setError("WebSocket connection error");
        console.error("WebSocket error:", error);
      };

      setWs(websocket);
    } catch (error) {
      setError("Failed to create WebSocket connection");
      console.error("Error creating WebSocket:", error);
    }
  }, [endpoint]); // Remove 'ws' from dependencies to prevent infinite loop

  const disconnect = useCallback(() => {
    if (ws) {
      ws.close(1000, "Disconnected by user");
      setWs(null);
      setIsConnected(false);
      setError(null);
    }
  }, [ws]);

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close(1000, "Component unmounting");
      }
    };
  }, [ws]);

  return {
    data,
    isConnected,
    error,
    connect,
    disconnect,
  };
};

// Combined hook for service status widget
export const useServiceStatusWidget = (modalOpen: boolean = false) => {
  // Use REST API for basic status when modal is closed
  const {
    data: restData,
    isLoading,
    error: restError,
  } = useServiceStatus(!modalOpen);

  // Use WebSocket for real-time updates when modal is open
  const {
    data: wsData,
    isConnected,
    error: wsError,
    connect,
    disconnect,
  } = useServiceWebSocket("live");

  // Connect/disconnect WebSocket based on modal state
  useEffect(() => {
    if (modalOpen) {
      connect();
    } else {
      disconnect();
    }
  }, [modalOpen]); // Remove connect/disconnect from dependencies

  // Use WebSocket data when available and connected, otherwise use REST data
  const data = modalOpen && wsData ? wsData : restData;
  const error = wsError || restError;

  return {
    data,
    isLoading: !modalOpen ? isLoading : false,
    isConnected,
    error,
    hasRunningServices: (data as ServicesData)?.is_any_running || false,
    totalRunning: (data as ServicesData)?.summary?.total_running || 0,
  };
};

// Utility function to calculate service duration
const getServiceDuration = (service?: Service): string => {
  if (!service?.started_at) return "Unknown";

  const start = new Date(service.started_at);
  const end = service.completed_at
    ? new Date(service.completed_at)
    : new Date();
  const duration = Math.floor((end.getTime() - start.getTime()) / 1000);

  if (duration < 60) return `${duration}s`;
  if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;

  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor((duration % 3600) / 60);
  return `${hours}h ${minutes}m`;
};
