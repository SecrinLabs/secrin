"use client";

import { useState } from "react";
import { Input } from "@workspace/ui/components/input";
import { Button } from "@workspace/ui/components/button";
import { Alert, AlertDescription } from "@workspace/ui/components/alert";

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSend() {
    setError("");
    setResponse("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: message }),
      });
      if (!res.ok) {
        setError("Failed to get response.");
      } else {
        const data = await res.json();
        setResponse(data?.answer);
      }
    } catch (err) {
      setError("Network error.");
    }
    setMessage("");
    setLoading(false);
  }

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white dark:bg-zinc-900 rounded-lg shadow">
      <h1 className="text-2xl font-bold mb-4">Chat with DevSecrin</h1>
      <div className="flex gap-2 mb-4">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message..."
          className="flex-1"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !loading) handleSend();
          }}
        />
        <Button onClick={handleSend} disabled={loading || !message}>
          {loading ? "Sending..." : "Send"}
        </Button>
      </div>
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {response && (
        <div className="p-4 bg-zinc-100 dark:bg-zinc-800 rounded">
          <strong>Response:</strong>
          <div className="mt-2 whitespace-pre-wrap">{response}</div>
        </div>
      )}
    </div>
  );
}
