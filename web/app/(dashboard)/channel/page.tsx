"use client";

import { useState } from "react";
import { Clock, Loader2, Plug } from "lucide-react";

import { Icons } from "@/components/Icons";
import { Button } from "@/components/ui/button";

interface Channel {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  connected: boolean;
}

const initialChannels: Channel[] = [
  {
    id: "chat",
    name: "Chat",
    icon: Icons.chat,
    description: "chat directly in secrin app.",
    connected: false,
  },
  {
    id: "github",
    name: "Github",
    icon: Icons.github,
    description: "Stay connected inside Github.",
    connected: false,
  },
];

export default function Page() {
  const [channels, setChannels] = useState<Channel[]>(initialChannels);
  const [loadingButtons, setLoadingButtons] = useState<Record<string, boolean>>(
    {}
  );

  // Placeholder: handle connecting to a channel
  const handleConnect = async (channelId: string) => {
    setLoadingButtons((prev) => ({ ...prev, [channelId]: true }));
    // TODO: Add API call to connect the channel
    setTimeout(() => {
      setChannels((prev) =>
        prev.map((c) => (c.id === channelId ? { ...c, connected: true } : c))
      );
      setLoadingButtons((prev) => ({ ...prev, [channelId]: false }));
    }, 1000);
  };

  // Placeholder: handle disconnecting a channel
  const handleDisconnect = async (channelId: string) => {
    setLoadingButtons((prev) => ({ ...prev, [channelId]: true }));
    // TODO: Add API call to disconnect the channel
    setTimeout(() => {
      setChannels((prev) =>
        prev.map((c) => (c.id === channelId ? { ...c, connected: false } : c))
      );
      setLoadingButtons((prev) => ({ ...prev, [channelId]: false }));
    }, 1000);
  };

  return (
    <div className="flex flex-1 flex-col gap-6 p-6 max-w-5xl mx-auto">
      <div className="space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">Channels</h1>
        <p className="text-muted-foreground text-lg">
          Connect channels like Github, Slack, or Teams to interact with your
          data directly where you work.
        </p>
      </div>

      <div className="space-y-4">
        {channels.map((channel) => {
          const Icon = channel.icon;
          const isLoading = loadingButtons[channel.id] ?? false;

          return (
            <div
              key={channel.id}
              className="flex items-center justify-between rounded-xl border bg-card shadow-sm p-5 hover:shadow-md transition"
            >
              <div className="flex items-start gap-4">
                <div className="rounded-lg bg-muted p-3">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <div className="font-semibold text-lg">{channel.name}</div>
                  <p className="text-sm text-muted-foreground">
                    {channel.description}
                  </p>
                </div>
              </div>
              <Button
                size="sm"
                variant={channel.connected ? "secondary" : "default"}
                className="gap-2 cursor-pointer"
                onClick={() =>
                  channel.connected
                    ? handleDisconnect(channel.id)
                    : handleConnect(channel.id)
                }
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />{" "}
                    {channel.connected ? "Disconnecting" : "Connecting"}
                  </>
                ) : (
                  <>
                    <Plug className="h-4 w-4" />{" "}
                    {channel.connected ? "Disconnect" : "Connect"}
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
              More channels coming soon
            </div>
            <p className="text-sm text-muted-foreground/80">
              Stay tuned — we’re adding more ways to connect.
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
