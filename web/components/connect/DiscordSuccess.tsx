"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, XCircle, LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Icons } from "../Icons";
import { saveDiscordTokens } from "@/service/connect";

export default function DiscordSuccess({ userId }: { userId?: string | null }) {
  const [status, setStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");

  const searchParams = useSearchParams();
  const discord_code = searchParams.get("code");
  const discord_guild_id = searchParams.get("guild_id");

  const saveToken = useCallback(async () => {
    try {
      if (!discord_guild_id || !discord_code) throw new Error("Invalid token");
      if (!userId) throw new Error("User not authenticated");

      setStatus("loading");

      const res = await saveDiscordTokens({
        code: discord_code,
        guild_id: discord_guild_id,
      });

      if (!res.success)
        throw new Error(res.message || "Failed to save discord info");

      setStatus("success");
      setMessage(res.message || "Discord connected successfully");
    } catch (err: unknown) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Unexpected error");
    }
  }, [discord_guild_id, discord_code, userId]);

  useEffect(() => {
    if (discord_code && discord_guild_id && userId) {
      void saveToken();
    }
  }, [discord_guild_id, discord_code, userId, saveToken]);

  if (!userId) {
    return (
      <main className="min-h-screen bg-muted flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
              <Icons.discord
                aria-hidden="true"
                className="h-6 w-6 text-foreground"
              />
              <span className="sr-only">Discord</span>
            </div>
            <CardTitle className="text-balance">Sign in required</CardTitle>
            <CardDescription className="text-pretty">
              Please sign in to connect your Discord account.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertTitle>Authentication needed</AlertTitle>
              <AlertDescription>
                We couldn&apos;t detect an active session. After you sign in,
                return to this page and try again.
              </AlertDescription>
            </Alert>
            <div className="flex items-center justify-center gap-3">
              <Button asChild>
                <Link href="/api/auth/signin" aria-label="Sign in">
                  Sign in
                </Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/">Go home</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    );
  }

  if (status === "loading" || status === "idle") {
    return (
      <main className="min-h-screen bg-muted flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
              <Icons.discord
                aria-hidden="true"
                className="h-6 w-6 text-foreground"
              />
              <span className="sr-only">Discord</span>
            </div>
            <CardTitle className="text-balance">Connecting Discord…</CardTitle>
            <CardDescription className="text-pretty">
              Connecting your Discord account with secrin.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div
              className="flex items-center gap-3"
              role="status"
              aria-live="polite"
            >
              <LoaderCircle className="h-5 w-5 animate-spin text-foreground/70" />
              <span className="text-sm text-muted-foreground">
                Working on it…
              </span>
            </div>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Verifying your session</li>
              <li>• Linking installation to your profile</li>
              <li>• Finalizing connection</li>
            </ul>
          </CardContent>
        </Card>
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="min-h-screen bg-muted flex items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-2">
            <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
              <XCircle aria-hidden="true" className="h-6 w-6 text-red-600" />
              <span className="sr-only">Error</span>
            </div>
            <CardTitle className="text-balance">We hit a snag</CardTitle>
            <CardDescription className="text-pretty">
              We couldn’t save your info. Try again below.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive" role="alert" aria-live="assertive">
              <AlertTitle>Token save failed</AlertTitle>
              <AlertDescription>
                {message || "An unexpected error occurred."}
              </AlertDescription>
            </Alert>

            <div className="flex items-center justify-between gap-3">
              <Button
                variant="default"
                onClick={saveToken}
                className="min-w-24"
                aria-label="Retry saving token"
              >
                Retry
              </Button>
              <div className="flex items-center gap-2">
                <Button variant="outline" asChild>
                  <Link href="/">Go home</Link>
                </Button>
                <Button variant="ghost" asChild>
                  <a
                    href="mailto:jenil@secrinlabs.com"
                    aria-label="Contact support"
                  >
                    Contact support
                  </a>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-muted flex items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto h-12 w-12 rounded-full bg-background shadow-sm ring-1 ring-border flex items-center justify-center">
            <CheckCircle2
              aria-hidden="true"
              className="h-7 w-7 text-green-600"
            />
            <span className="sr-only">Success</span>
          </div>
          <CardTitle className="text-balance">You’re all set!</CardTitle>
          <CardDescription className="text-pretty">
            {message || "Token saved successfully."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md p-3 bg-background ring-1 ring-border">
            <div className="flex items-center gap-2 text-sm">
              <Icons.discord
                className="h-4 w-4 text-foreground/80"
                aria-hidden="true"
              />
              <span className="text-muted-foreground">
                Your Discord app is now linked to your account.
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
