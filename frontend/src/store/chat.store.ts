import { create } from "zustand";
import { API_BASE_URL } from "../lib/api";
import { useAuthStore } from "./auth.store";

interface Message {
  id: string;
  content: string;
  timestamp: Date;
  sender: "user" | "system";
}

interface ChatState {
  messages: Message[];
  loading: boolean;
  error: string | null;
  addMessage: (message: Omit<Message, "id" | "timestamp">) => void;
  clearMessages: () => void;
  sendMessage: (content: string) => Promise<void>;
  loadMessages: () => Promise<void>;
}

const parseResponse = async <T>(response: Response): Promise<T> => {
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Error en la API");
  }
  return payload as T;
};

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  loading: false,
  error: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: Date.now().toString(),
          timestamp: new Date(),
        },
      ],
    })),

  clearMessages: () => set({ messages: [] }),

  sendMessage: async (content: string) => {
    const token = useAuthStore.getState().token;
    if (!token) throw new Error("Usuario no autenticado");

    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE_URL}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ content, sender: "user" }),
      });

      const newMessage = await parseResponse<MessageResponse>(response);
      get().addMessage({
        content: newMessage.content,
        sender: newMessage.sender as "user" | "system",
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Error desconocido",
      });
      throw error;
    } finally {
      set({ loading: false });
    }
  },

  loadMessages: async () => {
    const token = useAuthStore.getState().token;
    if (!token) throw new Error("Usuario no autenticado");

    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE_URL}/messages`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const messages = await parseResponse<MessageResponse[]>(response);
      const formattedMessages = messages.map((msg) => ({
        id: msg.id.toString(),
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        sender: msg.sender as "user" | "system",
      }));
      set({ messages: formattedMessages });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Error desconocido",
      });
      throw error;
    } finally {
      set({ loading: false });
    }
  },
}));

interface MessageResponse {
  id: number;
  user_id: number;
  content: string;
  timestamp: string;
  sender: string;
}
