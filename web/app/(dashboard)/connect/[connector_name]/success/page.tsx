"use client";

import { useSearchParams } from "next/navigation";

import GithubSuccess from "@/components/connect/GithubSuccess";
import { useSession } from "next-auth/react";
import React from "react";

function Page() {
  //const params = useParams(); // gets dynamic segments
  const searchParams = useSearchParams(); // gets query string params
  const { data: session } = useSession();

  //const name = params.connector_name;
  const installationId = searchParams.get("installation_id");

  return (
    <div>
      <GithubSuccess
        installation_token={installationId}
        userId={session?.user.id}
      />
    </div>
  );
}

export default Page;
