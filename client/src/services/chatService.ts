// src/services/chatService.ts
import apiClient from './api';

//
// 2a) TS interface for ChatRequest  ➞  { conversation_id?: number; message: string }
export interface ChatRequest {
  conversation_id?: number;
  message: string;
}

//
// 2b) TS interface for ChatResponse  ➞  { conversation_id: number; reply: string }
export interface ChatResponse {
  conversation_id: number;
  reply: string;
}

export interface ConversationSummary {
  conversation_id: number;
  created_at: string;
  summary: string;
}

export interface MessageItem {
  role: string;      // "user" or "assistant"
  content: string;
  created_at: string; // ISO 8601 string
}


export interface ConversationHistory {
  conversation_id: number;
  messages: MessageItem[];
}

export async function chatService(
  payload: ChatRequest
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/chat', payload);
  return response.data;
}

export async function getConversationsList(): Promise<ConversationSummary[]> {
  const response = await apiClient.get<ConversationSummary[]>("/conversations");
  return response.data;
}

//
// 2.2.2. Fetch full history of one conversation
export async function getConversationHistory(
  conversation_id: number
): Promise<ConversationHistory> {
  const response = await apiClient.get<ConversationHistory>(
    `/conversations/${conversation_id}`
  );
  return response.data;
}
