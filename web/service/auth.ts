// api/auth.ts
import env from "@/config/env";
import { getFriendlyErrorMessage } from "@/lib/HttpError";
import {
  CommonAPIResponse,
  PasswordCheckRequest,
  PasswordCheckResponse,
  UserLoginRequest,
} from "@/types";

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

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new AuthApiError("Unable to connect to auth service", 0);
    }

    throw new AuthApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}

// Service function
export async function checkPasswordAndSave(
  request: PasswordCheckRequest
): Promise<CommonAPIResponse<PasswordCheckResponse>> {
  try {
    const response = await fetch(`${env.api.url}/api/auth/set-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const friendlyMessage =
        errorData.message || response.statusText || "Something went wrong";

      throw new AuthApiError(friendlyMessage, response.status, errorData);
    }

    const data = await response.json();

    // Validate structure
    if (typeof data.success !== "boolean") {
      throw new AuthApiError("Invalid response format from server", 500, data);
    }

    return data as CommonAPIResponse<PasswordCheckResponse>;
  } catch (error) {
    if (error instanceof AuthApiError) {
      throw error;
    }

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new AuthApiError("Unable to connect to auth service", 0);
    }

    throw new AuthApiError(
      error instanceof Error ? error.message : "Unknown error occurred",
      500
    );
  }
}
