// Make CommonAPIResponse generic
export interface CommonAPIResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
}
