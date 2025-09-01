"use client";

import { saveInstallationToken } from "@/service/connect";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

export default function GithubSuccess({
  installation_token,
}: {
  installation_token?: string | null;
}) {
  const { data: session, status: sessionStatus } = useSession();

  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function saveToken() {
      try {
        if (!installation_token) {
          throw new Error("invalid token");
        }

        if (sessionStatus !== "authenticated") {
          throw new Error("User not authenticated");
        }

        console.log(session.user);

        // Assuming your session.user contains an id field
        const userId = session.user.id;
        if (!userId) {
          throw new Error("User ID not found in session");
        }

        const parsedUserId = Number(userId);
        if (isNaN(parsedUserId)) {
          throw new Error("Invalid user id");
        }

        const res = await saveInstallationToken({
          installation_token,
          user_id: parsedUserId,
        });

        if (!res.success) {
          throw new Error(res.message);
        }

        setStatus("success");
        setMessage("Token saved successfully");
      } catch (err: unknown) {
        if (err instanceof Error) {
          setStatus("error");
          setMessage(err.message);
        } else {
          setStatus("error");
          setMessage("Unexpected error");
        }
      }
    }

    if (installation_token && sessionStatus === "authenticated") {
      saveToken();
    }
  });

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold">Saving GitHub Installation Token</h1>
      {status === "loading" && <p>Processing...</p>}
      {status === "success" && <p className="text-green-600">{message}</p>}
      {status === "error" && <p className="text-red-600">Error: {message}</p>}
    </div>
  );
}
