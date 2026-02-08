"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Check, Github, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiClient } from "@/lib/api-client";

export default function OnboardingPage() {
  const { data: session, update } = useSession();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [installationChecked, setInstallationChecked] = useState(false);

  // Check if already installed
  useEffect(() => {
    const checkInstallation = async () => {
      try {
        const res = await ApiClient.get<{ installed: boolean }>("/github/installation/callback");
        if (res.installed) {
          setInstallationChecked(true);
          setStep(2); // Move to completion step if installed
        }
      } catch (err) {
        console.error("Failed to check installation", err);
      }
    };
    if (session) {
      checkInstallation();
    }
  }, [session]);

  const handleComplete = async () => {
    setLoading(true);
    try {
      // Call API to mark onboarding as complete
      await ApiClient.post("/user/complete-onboarding", {});
      
      // Update session to reflect isNew = false
      await update({ isNew: false });
      
      router.push("/dashboard");
    } catch (err) {
      console.error("Failed to complete onboarding", err);
      setLoading(false);
    }
  };

  const steps = [
    {
      id: 1,
      title: "Connect GitHib",
      description: "Link your GitHub account to Secrin",
      completed: !!session?.user,
    },
    {
      id: 2,
      title: "Install GitHub App",
      description: "Install our GitHub App to manage repositories",
      completed: installationChecked,
    },
    {
      id: 3,
      title: "All Set",
      description: "You are ready to use Secrin",
      completed: false, // Final step
    },
  ];

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-muted/20">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle className="text-2xl">Welcome to Secrin</CardTitle>
          <CardDescription>
            Complete these steps to get started with your account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Steps Indicator */}
          <div className="space-y-4">
            {steps.map((s, idx) => (
              <div
                key={s.id}
                className={`flex items-center gap-3 p-3 rounded-lg border ${
                  s.completed
                    ? "bg-primary/5 border-primary/20"
                    : idx + 1 === step || (idx===0 && step===1) // Show current step active
                    ? "bg-card border-primary"
                    : "bg-muted/50 border-transparent opacity-60"
                }`}
              >
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full border ${
                    s.completed
                      ? "bg-primary text-primary-foreground border-primary"
                      : "border-muted-foreground"
                  }`}
                >
                  {s.completed ? <Check className="h-4 w-4" /> : s.id}
                </div>
                <div>
                  <h4 className="font-medium">{s.title}</h4>
                  <p className="text-xs text-muted-foreground">
                    {s.description}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Action Area */}
          <div className="pt-4">
            {!session ? (
               <Button className="w-full" onClick={() => router.push("/api/auth/signin")}>
                <Github className="mr-2 h-4 w-4" /> Sign in with GitHub
               </Button>
            ) : !installationChecked ? (
               <div className="space-y-2">
                 <p className="text-sm text-muted-foreground text-center">
                   You need to install the Secrin GitHub App to continue.
                 </p>
                 <Button className="w-full" asChild>
                   {/* Replace with actual GitHub App Install URL */}
                   <a href="https://github.com/apps/secrinbot" target="_blank" rel="noopener noreferrer">
                     Install GitHub App <ArrowRight className="ml-2 h-4 w-4" />
                   </a>
                 </Button>
                 <div className="flex justify-center mt-2">
                    <Button variant="ghost" size="sm" onClick={() => window.location.reload()}>
                        I've installed it, continue
                    </Button>
                 </div>
               </div>
            ) : (
                <div className="space-y-2">
                    <p className="text-sm text-muted-foreground text-center">
                        Everything looks good!
                    </p>
                    <Button className="w-full" onClick={handleComplete} disabled={loading}>
                        {loading ? "Finalizing..." : "Go to Dashboard"}
                    </Button>
                </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
