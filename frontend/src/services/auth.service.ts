import { API_BASE_URL } from "../lib/api";
import {
  LoginPayload,
  LoginResponse,
  RegisterPayload,
  RegisterResponse,
  UserProfile,
  ApiError,
} from "../types/auth.types";

const parseResponse = async <T>(response: Response): Promise<T> => {
  const payload = await response.json();
  if (!response.ok) {
    const apiError = payload as ApiError;
    throw new Error(apiError.detail || "Error en la API");
  }
  return payload as T;
};

export const authService = {
  register: async (payload: RegisterPayload): Promise<RegisterResponse> => {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    return parseResponse<RegisterResponse>(response);
  },

  login: async (payload: LoginPayload): Promise<LoginResponse> => {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    return parseResponse<LoginResponse>(response);
  },

  me: async (token: string): Promise<UserProfile> => {
    const response = await fetch(`${API_BASE_URL}/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return parseResponse<UserProfile>(response);
  },
};
