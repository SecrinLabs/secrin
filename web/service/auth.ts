// api/auth.ts
import env from "@/config/env";
import { getFriendlyErrorMessage } from "@/lib/HttpError";

export interface UserLoginRequest {
  email: string;
  password: string;
}

// export interface User {
//   id: number;
//   email: string;
//   username: string;
// }

// export interface UserLoginResponse {
//   user: User | null;
// }

export interface ApiError {
  message: string;
  status: number;
}

export class AuthApiError extends Error {
  constructor(message: string, public status: number, public data?: unknown) {
    super(message);
    this.name = "AuthApiError";
  }
}

export async function loginUser(request: UserLoginRequest) {
  try {
    const response = await fetch(`${env.api.url}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const friendlyMessage = getFriendlyErrorMessage(
        response.status,
        errorData.message || response.statusText
      );

      throw new AuthApiError(friendlyMessage, response.status, errorData);
    }

    const data = await response.json();

    // If we get an error response with a detail field
    if (data.detail) {
      throw new AuthApiError(data.detail, response.status, data);
    }

    // Validate response structure
    if (data.user) {
      throw new AuthApiError("Invalid response format from server", 500, data);
    }

    return data;
  } catch (error) {
    if (error instanceof AuthApiError) {
      throw error;
    }

    console.error("Login error:", error);

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new AuthApiError("Unable to connect to auth service", 0);
    }

    throw new AuthApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}
