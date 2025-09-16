"use client";

import { useState } from "react";
import { Icons } from "@/components/Icons";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

const GITHUB_APP_URL = "https://github.com/apps/your-devsecrin-app"; // replace with actual app URL

interface Connector {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  connected: boolean;
}

const connectors: Connector[] = [
  {
    id: "github",
    name: "GitHub",
    icon: Icons.github,
    description:
      "Connect to your GitHub repositories for code analysis and security scanning.",
    connected: false,
  },
  {
    id: "twitter",
    name: "Twitter",
    icon: Icons.twitter,
    description: "Connect to Twitter for social media security monitoring.",
    connected: false,
  },
  // More connectors can be added here as more icons become available
];

export default function Page() {
  const [activeConnectors, setActiveConnectors] = useState<string[]>([]);

  const handleConnectorToggle = async (
    connectorId: string,
    isActive: boolean
  ) => {
    if (isActive) {
      if (connectorId === "github") {
        window.location.href = GITHUB_APP_URL;
        return;
      }
      // Add connector
      setActiveConnectors((prev) => [...prev, connectorId]);
      // Here you would typically make an API call to connect the service
      // await fetch(`/api/connect/${connectorId}`, { method: "POST" });
    } else {
      // Remove connector
      setActiveConnectors((prev) => prev.filter((id) => id !== connectorId));
      // Here you would typically make an API call to disconnect the service
      // await fetch(`/api/disconnect/${connectorId}`, { method: "POST" });
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-6 p-6 max-w-7xl mx-auto">
      <div className="space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">
          Service Connections
        </h1>
        <p className="text-muted-foreground text-lg">
          Connect your development tools and services to enable comprehensive
          security analysis.
        </p>
      </div>

      <div className="rounded-xl border bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-[80px]"></TableHead>
              <TableHead className="font-semibold">Service</TableHead>
              <TableHead className="hidden md:table-cell font-semibold">
                Description
              </TableHead>
              <TableHead className="w-[140px] text-right font-semibold">
                Status
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {connectors.map((connector) => (
              <TableRow
                key={connector.id}
                className="group transition-colors hover:bg-muted/50"
              >
                <TableCell className="py-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                    <connector.icon className="h-6 w-6" />
                  </div>
                </TableCell>
                <TableCell className="font-medium">
                  <div className="flex flex-col">
                    <span>{connector.name}</span>
                    <span className="text-sm text-muted-foreground md:hidden">
                      {connector.description}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="hidden md:table-cell text-muted-foreground">
                  {connector.description}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <span
                      className={`text-sm font-medium ${
                        activeConnectors.includes(connector.id)
                          ? "text-green-600 dark:text-green-500"
                          : "text-muted-foreground"
                      }`}
                    >
                      {activeConnectors.includes(connector.id)
                        ? "Connected"
                        : "Disconnected"}
                    </span>
                    <Button
                      variant={
                        activeConnectors.includes(connector.id)
                          ? "secondary"
                          : "outline"
                      }
                      size="sm"
                      className={`min-w-[100px] transition-all ${
                        activeConnectors.includes(connector.id)
                          ? "hover:bg-destructive hover:text-destructive-foreground"
                          : "hover:bg-primary hover:text-primary-foreground"
                      }`}
                      onClick={() =>
                        handleConnectorToggle(
                          connector.id,
                          !activeConnectors.includes(connector.id)
                        )
                      }
                    >
                      {activeConnectors.includes(connector.id)
                        ? "Disconnect"
                        : "Connect"}
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
