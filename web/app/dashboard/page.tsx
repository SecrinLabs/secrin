"use client";

import React from "react";
import { useSession } from "next-auth/react";

export default function Page() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  if (status === "unauthenticated") {
    return <div>You are not logged in</div>;
  }

  return (
    <div>
      <h1>User Info</h1>
      <pre>{JSON.stringify(session?.user, null, 2)}</pre>
    </div>
  );
}
