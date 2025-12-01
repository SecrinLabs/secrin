"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GitHubConnectCard } from "@/components/integrations/github/github-connect-card";

export default function IntegrationsPage() {
  return (
    <div className="container mx-auto py-10 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">App Integrations</h1>
        <p className="text-muted-foreground mt-2">
          Connect your favorite tools to Secrin to enhance your knowledge graph.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* GitHub Integration */}
        <GitHubConnectCard />

        {/* Placeholder for future integrations */}
        <Card className="flex flex-col opacity-60">
          <CardHeader>
            <CardTitle>Jira</CardTitle>
            <CardDescription>Coming Soon</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Connect Jira to link issues with code changes.
            </p>
          </CardContent>
          <CardFooter>
            <Button disabled variant="outline" className="w-full">
              Coming Soon
            </Button>
          </CardFooter>
        </Card>

        <Card className="flex flex-col opacity-60">
          <CardHeader>
            <CardTitle>Slack</CardTitle>
            <CardDescription>Coming Soon</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Get notifications and query the knowledge graph from Slack.
            </p>
          </CardContent>
          <CardFooter>
            <Button disabled variant="outline" className="w-full">
              Coming Soon
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
