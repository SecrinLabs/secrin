import Link from "next/link";
import { ArrowRight, Network, Puzzle } from "lucide-react";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8 bg-background text-foreground">
      <div className="max-w-2xl w-full space-y-8 text-center">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            Welcome to Secrin
          </h1>
          <p className="text-lg text-muted-foreground">
            Your security dashboard is currently under construction. In the
            meantime, explore our graph visualization and integration settings.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 mt-8">
          <Link
            href="/graph"
            className="group relative flex flex-col items-center justify-center rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm transition-all hover:shadow-md hover:border-primary/50"
          >
            <div className="mb-4 rounded-full bg-primary/10 p-3 text-primary group-hover:bg-primary/20">
              <Network className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-xl font-semibold">Graph View</h3>
            <p className="text-sm text-muted-foreground text-center mb-4">
              Visualize relationships and dependencies in your security graph.
            </p>
            <span className="flex items-center text-sm font-medium text-primary">
              Go to Graph{" "}
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>

          <Link
            href="/integrations"
            className="group relative flex flex-col items-center justify-center rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm transition-all hover:shadow-md hover:border-primary/50"
          >
            <div className="mb-4 rounded-full bg-primary/10 p-3 text-primary group-hover:bg-primary/20">
              <Puzzle className="h-6 w-6" />
            </div>
            <h3 className="mb-2 text-xl font-semibold">Integrations</h3>
            <p className="text-sm text-muted-foreground text-center mb-4">
              Manage your connected tools and data sources.
            </p>
            <span className="flex items-center text-sm font-medium text-primary">
              Manage Integrations{" "}
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
