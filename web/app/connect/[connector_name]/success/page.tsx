"use client";

import { useParams, useSearchParams } from "next/navigation";

import GithubSuccess from "@/components/connect/GithubSuccess";
import React from "react";

function Page() {
  const params = useParams(); // gets dynamic segments
  const searchParams = useSearchParams(); // gets query string params

  const name = params.name; // [name]
  const installationId = searchParams.get("installation_id");

  return (
    <div>
      <h1>Success Page</h1>
      <p>Name: {name}</p>
      <p>Installation ID: {installationId}</p>
      <GithubSuccess installation_token={installationId} />
    </div>
  );
}

export default Page;
