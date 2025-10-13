"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Clock, Loader2, Plug } from "lucide-react";
import { useRouter } from "next/navigation";

import { Icons } from "@/components/Icons";
import { Button } from "@/components/ui/button";
import { disconnectService, getUserIntegrations } from "@/service/connect";
import { DisconnectServiceRequest } from "@/types";

const GITHUB_APP_URL = "https://github.com/apps/secrinbot"; // replace with actual app URL

interface Connector {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  connected: boolean;
}

const initialConnectors: Connector[] = [
  {
    id: "github",
    name: "GitHub",
    icon: Icons.github,
    description: "Connect your GitHub account.",
    connected: false,
  },
  {
    id: "discord",
    name: "Discord",
    icon: Icons.discord,
    description: "Connect your Discord account.",
    connected: false,
  },
];

export default function Page() {
  const [connectors, setConnectors] = useState<Connector[]>(initialConnectors);
  const [loadingButtons, setLoadingButtons] = useState<Record<string, boolean>>(
    {}
  );
  const router = useRouter();
  const { data: session, status } = useSession();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchIntegrations = async () => {
      if (status === "loading") return;
      try {
        setLoading(true);
        if (!session?.user.userGUID) {
          return;
        }

        const response = await getUserIntegrations({
          user_guid: session?.user.userGUID,
        });

        const activeIds = response.data?.integrations.map((i) => i.type) ?? [];

        setConnectors((prev) =>
          prev.map((c) => ({
            ...c,
            connected: activeIds.includes(c.id),
          }))
        );
      } catch (error) {
        console.error("Error fetching integrations:", error);
        setConnectors((prev) => prev.map((c) => ({ ...c, connected: false })));
      } finally {
        setLoading(false); // ✅ stop loading after API resolves
      }
    };

    fetchIntegrations();
  }, [status, session?.user?.id]);

  // Handle connection
  const handleConnect = async (connectorId: string) => {
    try {
      if (connectorId === "github") {
        router.push(GITHUB_APP_URL);
      }

      setConnectors((prev) =>
        prev.map((c) => (c.id === connectorId ? { ...c, connected: true } : c))
      );
    } catch (error) {
      console.error("Error connecting:", error);
    } finally {
      setLoadingButtons((prev) => ({ ...prev, [connectorId]: false }));
    }
  };

  const handleDisconnect = async (connectorId: string) => {
    if (!session?.user.userGUID) return;
    setLoadingButtons((prev) => ({ ...prev, [connectorId]: true }));

    try {
      const request: DisconnectServiceRequest = {
        user_guid: session.user.userGUID || "",
        service_type: connectorId,
      };

      const response = await disconnectService(request);

      if (!response.success) {
        console.error("Failed to disconnect:", response.message);
        return;
      }

      if (connectorId === "github") {
        router.push(GITHUB_APP_URL);
        return;
      }

      setConnectors((prev) =>
        prev.map((c) => (c.id === connectorId ? { ...c, connected: false } : c))
      );
    } catch (error) {
      console.error("Error disconnecting:", error);
    } finally {
      setLoadingButtons((prev) => ({ ...prev, [connectorId]: false }));
    }
  };

  if (status === "loading" || loading) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[200px]">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Loading...</span>
      </div>
    ); // ✅ central loading UI
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6 max-w-5xl mx-auto">
      <div className="space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">
          Service Connections
        </h1>
        <p className="text-muted-foreground text-lg">
          Connect your development tools and services to enhance your workflow.
        </p>
      </div>

      <div className="space-y-4">
        {connectors.map((connector) => {
          const Icon = connector.icon;
          const isLoading = loadingButtons[connector.id] ?? false;

          return (
            <div
              key={connector.id}
              className="flex items-center justify-between rounded-xl border bg-card shadow-sm p-5 hover:shadow-md transition"
            >
              <div className="flex items-start gap-4">
                <div className="rounded-lg bg-muted p-3">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <div className="font-semibold text-lg">{connector.name}</div>
                  <p className="text-sm text-muted-foreground">
                    {connector.description}
                  </p>
                </div>
              </div>
              <Button
                size="sm"
                variant={connector.connected ? "secondary" : "default"}
                className="gap-2 cursor-pointer"
                onClick={() =>
                  connector.connected
                    ? handleDisconnect(connector.id)
                    : handleConnect(connector.id)
                }
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />{" "}
                    {connector.connected ? "Disconnecting" : "Connecting"}
                  </>
                ) : (
                  <>
                    <Plug className="h-4 w-4" />{" "}
                    {connector.connected ? "Disconnect" : "Connect"}
                  </>
                )}
              </Button>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between rounded-xl border-2 border-dashed border-muted bg-muted/30 p-5">
        <div className="flex items-start gap-4">
          <div className="rounded-lg bg-muted p-3">
            <Clock className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <div className="font-semibold text-lg text-muted-foreground">
              More integrations coming soon
            </div>
            <p className="text-sm text-muted-foreground/80">
              Stay tuned — we’re adding more services to connect with.
            </p>
          </div>
        </div>
        <Button disabled variant="outline" className="gap-2" size="sm">
          <Plug className="h-4 w-4" />
          Coming Soon
        </Button>
      </div>
    </div>
  );
}
