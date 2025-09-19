import { CheckCircle, Shield, Zap, Plug } from "lucide-react";

import { LoginForm } from "@/components/auth/login-form";
import { Badge } from "@/components/ui/badge";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex">
      {/* Left Section - Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-10 bg-background">
        <div className="w-full max-w-sm">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold text-foreground mb-2">
              Welcome back
            </h1>
            <p className="text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>
          <LoginForm />
        </div>
      </div>

      {/* Right Section - Devsecrin Connect Info */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-primary/5 via-accent/5 to-secondary/10 items-center justify-center p-10">
        <div className="max-w-md text-center space-y-8">
          {/* Hero Content */}
          <div className="space-y-4">
            <Badge variant="secondary" className="mb-4">
              Devsecrin Connect
            </Badge>
            <h2 className="text-3xl font-bold text-foreground text-balance">
              Connect your tools, unlock your workflow
            </h2>
            <p className="text-lg text-muted-foreground text-pretty">
              Link your favorite developer services — GitHub, Jira, Slack, and
              more — so Devsecrin can bring all your data together in one place.
            </p>
          </div>

          {/* Feature List */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-left">
              <div className="flex-shrink-0 w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                <Shield className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">
                  Secure integrations
                </h3>
                <p className="text-sm text-muted-foreground">
                  Your connected accounts are protected with enterprise-grade
                  security and never exposed directly.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-left">
              <div className="flex-shrink-0 w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                <Zap className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">
                  Instant productivity
                </h3>
                <p className="text-sm text-muted-foreground">
                  Get answers from your repos, tickets, and conversations
                  instantly — no more context switching.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-left">
              <div className="flex-shrink-0 w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                <Plug className="w-4 h-4 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">
                  Unified workflow
                </h3>
                <p className="text-sm text-muted-foreground">
                  Manage channels and sources in one place, and interact with
                  your data through chat or integrations.
                </p>
              </div>
            </div>
          </div>

          {/* Social Proof / Assurance */}
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
