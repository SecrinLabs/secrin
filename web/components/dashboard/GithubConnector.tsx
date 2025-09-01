import React from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

function GithubConnector() {
  return (
    <div>
      <Button asChild>
        <Link href="https://github.com/apps/devsecrin/installations/new">
          Connect Github
        </Link>
      </Button>
    </div>
  );
}

export default GithubConnector;
