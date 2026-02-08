"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiClient } from "@/lib/api-client";

function GitHubInstallSuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  const installationId = searchParams.get("installation_id");
  const setupAction = searchParams.get("setup_action");
  const code = searchParams.get("code");

  useEffect(() => {
    const saveInstallation = async () => {
      console.log("GitHub App Installation Callback:", {
        installationId,
        setupAction,
        code,
      });

      // If we have installation_id and setup_action=install, save it
      if (installationId && (setupAction === "install" || setupAction === "update")) {
        try {
          await ApiClient.post("/github/installation/callback", {
            installation_id: parseInt(installationId, 10),
            setup_action: setupAction,
            code: code,
          });
          setStatus("success");
        } catch (err) {
          console.error("Failed to save installation:", err);
          setError(err instanceof Error ? err.message : "Failed to save installation");
          setStatus("error");
        }
      } else {
        // If no params, check if we already have it installed
        try {
          const res = await ApiClient.get<{ installed: boolean }>("/github/installation/callback");
          if (res.installed) {
            setStatus("success");
          } else {
            setError("Missing installation parameters");
            setStatus("error");
          }
        } catch (err) {
          console.error("Failed to check installation:", err);
          setError("Failed to verify installation");
          setStatus("error");
        }
      }
    };

    saveInstallation();
  }, [installationId, setupAction, code]);

  const handleContinue = () => {
    router.push("/dashboard");
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-gradient-to-br from-background via-background to-muted/20">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          {status === "loading" && (
            <>
              <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
              <CardTitle>Processing...</CardTitle>
              <CardDescription>
                Setting up your GitHub App installation
              </CardDescription>
            </>
          )}
          
          {status === "success" && (
            <>
              <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <CardTitle className="text-green-600 dark:text-green-400">
                GitHub App Installed!
              </CardTitle>
              <CardDescription>
                The Secrin GitHub App has been successfully installed.
                You can now create projects with sample repositories.
              </CardDescription>
            </>
          )}
          
          {status === "error" && (
            <>
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <CardTitle className="text-destructive">
                Installation Issue
              </CardTitle>
              <CardDescription>
                {error || "There was an issue with the GitHub App installation. Please try again."}
              </CardDescription>
            </>
          )}
        </CardHeader>
        
        <CardContent className="text-center space-y-4">
          {installationId && status === "success" && (
            <p className="text-xs text-muted-foreground">
              Installation ID: {installationId}
            </p>
          )}
          
          <Button onClick={handleContinue} className="w-full">
            {status === "success" ? "Continue to Dashboard" : "Back to Dashboard"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

export default function GitHubInstallSuccessPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    }>
      <GitHubInstallSuccessContent />
    </Suspense>
  );
}
