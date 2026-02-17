"use client";

import Image from "next/image";
import { signIn } from "next-auth/react";
import { Github } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SITE } from "@/constants/site";
import { CONTENT } from "@/constants/content";

export default function LoginPage() {
  const handleGithubLogin = () => {
    signIn("github", { callbackUrl: "/dashboard" });
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex justify-center mb-2">
            <Image
              src={SITE.logo.svg}
              alt={`${SITE.name} logo`}
              width={40}
              height={40}
              className="dark:invert"
            />
          </div>
          <CardTitle className="text-2xl font-bold text-center">
            {CONTENT.login.heading}
          </CardTitle>
          <CardDescription className="text-center">
            {CONTENT.login.subheading}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <Button
            className="w-full"
            variant="outline"
            onClick={handleGithubLogin}
          >
            <Github className="mr-2 h-4 w-4" />
            {CONTENT.login.githubButton}
          </Button>
        </CardContent>
        <CardFooter>
          <div className="text-sm text-center text-muted-foreground w-full">
            By clicking continue, you agree to our{" "}
            <a href={CONTENT.login.termsLink} className="underline hover:text-primary">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href={CONTENT.login.privacyLink} className="underline hover:text-primary">
              Privacy Policy
            </a>
            .
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
