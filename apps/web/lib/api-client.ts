import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";
import { ENV } from "@/config/env";

export class ApiClient {
  private static client: AxiosInstance = axios.create({
    baseURL: ENV.API_URL,
    headers: {
      "Content-Type": "application/json",
    },
  });

  private static async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request(config);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        // Extract error message from API response if available
        const message =
          error.response?.data?.message ||
          error.message ||
          "API request failed";
        throw new Error(message);
      }
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("An unknown error occurred");
    }
  }

  static get<T>(endpoint: string, config?: AxiosRequestConfig) {
    return this.request<T>({ ...config, url: endpoint, method: "GET" });
  }

  static post<T>(endpoint: string, body: unknown, config?: AxiosRequestConfig) {
    return this.request<T>({
      ...config,
      url: endpoint,
      method: "POST",
      data: body,
    });
  }

  static put<T>(endpoint: string, body: unknown, config?: AxiosRequestConfig) {
    return this.request<T>({
      ...config,
      url: endpoint,
      method: "PUT",
      data: body,
    });
  }

  static delete<T>(endpoint: string, config?: AxiosRequestConfig) {
    return this.request<T>({ ...config, url: endpoint, method: "DELETE" });
  }
}
