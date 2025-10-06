"use client";

import { CheckCircle, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { checkPasswordAndSave } from "@/service/auth";
import { useSearchParams, useRouter } from "next/navigation";

export default function InvitePage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setIsLoading(true);

    try {
      const result = await checkPasswordAndSave({
        token: token as string,
        password: password,
      });

      console.log(result);
      setSuccess("Password set successfully! Redirecting to login...");

      // Redirect to login page after 1.5 seconds
      setTimeout(() => {
        router.push("/auth/login");
      }, 1500);
    } catch {
      setError("Failed to set password. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Section - Invite Form */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-10 bg-background">
        <div className="w-full max-w-sm">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold text-foreground mb-2">
              Set your password
            </h1>
            <p className="text-muted-foreground">
              Complete your account setup by creating a password
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="Enter password"
                required
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="Confirm password"
                required
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded text-sm text-destructive">
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div className="flex items-center gap-2 p-3 bg-primary/10 border border-primary/20 rounded text-sm text-primary">
                <CheckCircle className="w-4 h-4" />
                <span>{success}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary text-white py-2 rounded hover:bg-primary/90 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Setting Password...</span>
                </>
              ) : (
                <span>Set Password</span>
              )}
            </button>

            <p className="text-xs text-muted-foreground mt-2">
              In case you forget your password in the future, please contact{" "}
              <strong>help@secrinlabs.com</strong>
            </p>
          </form>
        </div>
      </div>

      {/* Right Section - Optional Info / Illustration */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/5 via-accent/5 to-secondary/10 items-center justify-center p-10">
        <div className="max-w-md text-center space-y-8">
          <Badge variant="secondary">Devsecrin Connect</Badge>
          <h2 className="text-3xl font-bold text-foreground text-balance">
            Connect your tools, unlock your workflow
          </h2>
          <p className="text-lg text-muted-foreground text-pretty">
            Link your favorite developer services — GitHub, Jira, Slack, and
            more — so Devsecrin can bring all your data together in one place.
          </p>

          <div className="pt-6 border-t border-border">
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <CheckCircle className="w-4 h-4 text-primary" />
              <span>Designed for developers</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
