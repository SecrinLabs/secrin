"use client";

import DiscordSuccess from "@/components/connect/DiscordSuccess";
import { useSession } from "next-auth/react";
import React, { Suspense } from "react";

function Page() {
  const { data: session } = useSession();
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <DiscordSuccess userId={session?.user.userGUID} />
      </Suspense>
    </div>
  );
}

export default Page;
