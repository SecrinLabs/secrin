"use client";

import GithubSuccess from "@/components/connect/GithubSuccess";
import { useSession } from "next-auth/react";
import React, { Suspense } from "react";

function Page() {
  const { data: session } = useSession();
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <GithubSuccess userId={session?.user.userGUID} />
      </Suspense>
    </div>
  );
}

export default Page;
