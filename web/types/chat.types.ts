export interface ChatRequest {
  question: string;
  conversation_id?: string;
}

export interface ChatResponse {
  answer: string;
  conversation_id?: string;
  timestamp?: string;
}

export interface ApiError {
  message: string;
  status: number;
}
