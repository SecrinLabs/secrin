"use client";

import { useState } from "react";
import env from "@/config/env";

export default function WaitlistPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    const formData = new FormData(e.currentTarget);
    const data = {
      name: formData.get("name") as string,
      email: formData.get("email") as string,
      subject: formData.get("role") as string,
    };

    try {
      const response = await fetch(
        `${env.api.url}/api/auth/new-user-interest`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      );

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Something went wrong");

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f6f5f4] px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-semibold text-gray-900 tracking-tight mb-2">
          Contact Us
        </h1>
        <p className="text-sm text-gray-600 mb-8 leading-relaxed">
          Get access to Secrin — the AI that remembers everything your team
          knows.
        </p>

        {success ? (
          <div className="border border-gray-200 rounded-lg p-6 text-center space-y-2">
            <p className="text-gray-900 font-medium">You’re on the list.</p>
            <p className="text-gray-500 text-sm">We’ll contact you soon.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              name="name"
              placeholder="Name"
              required
              disabled={isLoading}
              className="w-full border-b border-gray-300 bg-transparent py-2 text-sm placeholder-gray-500 focus:outline-none focus:border-gray-900 transition"
            />
            <input
              type="email"
              name="email"
              placeholder="Work email"
              required
              disabled={isLoading}
              className="w-full border-b border-gray-300 bg-transparent py-2 text-sm placeholder-gray-500 focus:outline-none focus:border-gray-900 transition"
            />
            <select
              name="role"
              required
              disabled={isLoading}
              className="w-full border-b border-gray-300 bg-transparent py-2 text-sm text-gray-700 focus:outline-none focus:border-gray-900 transition"
            >
              <option value="">Your role</option>
              <option value="developer">Developer</option>
              <option value="product-manager">Product Manager</option>
              <option value="team-lead">Team Lead</option>
              <option value="other">Other</option>
            </select>

            {error && (
              <p className="text-xs text-red-600 text-center mt-2">{error}</p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full border border-gray-900 text-gray-900 py-2 rounded-md text-sm font-medium tracking-wide hover:bg-gray-900 hover:text-white transition-all disabled:opacity-50"
            >
              {isLoading ? "Joining..." : "Join Waitlist"}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
