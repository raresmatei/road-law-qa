// src/services/authService.ts
import apiClient from './api';

//
// 1a) TS interface for RegisterRequest  ➞  { username: string; password: string }
export interface RegisterPayload {
  username: string;
  password: string;
}

//
// 1b) TS interface for RegisterResponse  ➞  { id: number; username: string }
export interface RegisterResponse {
  id: number;
  username: string;
}

//
// 1c) TS interface for LoginRequest  ➞  { username: string; password: string }
export interface LoginPayload {
  username: string;
  password: string;
}

//
// 1d) TS interface for LoginResponse  ➞  { access_token: string; token_type: string }
export interface LoginResponse {
  access_token: string;
  token_type: string; // typically "bearer"
  is_admin: boolean
}

//
// 1e) registerService(): POST /register → returns RegisterResponse
export async function registerService(
  payload: RegisterPayload
): Promise<RegisterResponse> {
  console.log('api client: ', apiClient)
  const response = await apiClient.post<RegisterResponse>('/register', payload);
  return response.data;
}

//
// 1f) loginService(): POST /login → returns LoginResponse
export async function loginService(
  payload: LoginPayload
): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/login', payload);
  return response.data;
}
