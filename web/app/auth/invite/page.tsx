"use client";

import { CheckCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";

export default function InvitePage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

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

    try {
      // TODO: call your API to set password
      setSuccess("Password set successfully! You can now log in.");
    } catch {
      setError("Failed to set password. Please try again.");
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
                className="w-full border rounded px-3 py-2"
                placeholder="Enter password"
                required
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
                className="w-full border rounded px-3 py-2"
                placeholder="Confirm password"
                required
              />
            </div>

            {error && <p className="text-sm text-red-500">{error}</p>}
            {success && <p className="text-sm text-green-500">{success}</p>}

            <button
              type="submit"
              className="w-full bg-primary text-white py-2 rounded hover:bg-primary/90 transition"
            >
              Set Password
            </button>

            <p className="text-xs text-muted-foreground mt-2">
              In case you forget your password in the future, please contact{" "}
              <strong>jenil@secrinlabs.com</strong>
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
