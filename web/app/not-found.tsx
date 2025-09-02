"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="flex min-h-[calc(100dvh-0px)] items-center justify-center px-6 py-16">
      <section
        aria-labelledby="not-found-title"
        className="w-full max-w-lg rounded-lg border bg-card p-8 text-card-foreground shadow-sm"
      >
        <div className="flex flex-col items-center text-center">
          <p className="font-medium text-muted-foreground">
            <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
              404 error
            </span>
          </p>

          <h1
            id="not-found-title"
            className="mt-2 text-6xl font-bold tracking-tight text-foreground"
            aria-label="404 page not found"
          >
            404
          </h1>

          <p className="mt-3 text-balance text-base text-muted-foreground">
            The page you’re looking for doesn’t exist or may have been moved.
          </p>

          <div className="mt-6 h-px w-full bg-border" />

          <div className="mt-8 flex flex-col-reverse items-center gap-3 sm:flex-row">
            <Button
              variant="outline"
              onClick={() => {
                if (
                  typeof window !== "undefined" &&
                  window.history.length > 1
                ) {
                  window.history.back();
                } else {
                  window.location.href = "/";
                }
              }}
            >
              Go back
            </Button>
            <Button asChild>
              <Link href="/">Go to homepage</Link>
            </Button>
          </div>
          <p className="mt-6 text-xs text-muted-foreground">
            If you believe this is an error, please contact support.
          </p>
        </div>
      </section>
    </main>
  );
}
