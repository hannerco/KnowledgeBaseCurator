import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: {
    localFilenames: string[];
    globalIds: string[];
  };
}

export interface Chat {
  id: string;
  backendId: number;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

interface DashboardState {
  currentChat: Chat | null;
  chats: Chat[];
  user: User | null;
  isAgentTyping: boolean;

  setCurrentChat: (chat: Chat | null) => void;
  addChat: (chat: Chat) => void;
  updateChat: (id: string, chat: Partial<Chat>) => void;
  deleteChat: (id: string) => void;
  setUser: (user: User | null) => void;
  setChats: (chats: Chat[]) => void;
  setAgentTyping: (value: boolean) => void;
  addAgentMessage: (chatId: string, content: string) => void;
  addChatFromBackend: (backendId: number, title: string, firstMessage: string) => string;
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      currentChat: null,
      chats: [],
      user: null,
      isAgentTyping: false,

      setCurrentChat: (chat) => set({ currentChat: chat }),

      setChats: (chats) =>
        set((state) => {
          const merged = chats.map((incoming) => {
            const existing = state.chats.find((c) => c.backendId === incoming.backendId);
            return existing && existing.messages.length > 0
              ? { ...incoming, messages: existing.messages }
              : incoming;
          });
          return { chats: merged };
        }),

      addChat: (chat) =>
        set((state) => ({ chats: [chat, ...state.chats] })),

      updateChat: (id, updatedChat) =>
        set((state) => ({
          chats: state.chats.map((chat) =>
            chat.id === id ? { ...chat, ...updatedChat } : chat
          ),
          currentChat:
            state.currentChat?.id === id
              ? { ...state.currentChat, ...updatedChat }
              : state.currentChat,
        })),

      deleteChat: (id) =>
        set((state) => ({
          chats: state.chats.filter((chat) => chat.id !== id),
          currentChat: state.currentChat?.id === id ? null : state.currentChat,
        })),

      setUser: (user) => set({ user }),

      setAgentTyping: (value) => set({ isAgentTyping: value }),

      addAgentMessage: (chatId, content) =>
        set((state) => {
          const agentMessage: Message = {
            id: Date.now().toString(),
            role: "assistant",
            content,
            timestamp: new Date(),
          };
          return {
            isAgentTyping: false,
            chats: state.chats.map((chat) =>
              chat.id === chatId
                ? { ...chat, messages: [...chat.messages, agentMessage], updatedAt: new Date() }
                : chat
            ),
            currentChat:
              state.currentChat?.id === chatId
                ? { ...state.currentChat, messages: [...state.currentChat.messages, agentMessage], updatedAt: new Date() }
                : state.currentChat,
          };
        }),

      addChatFromBackend: (backendId, title, firstMessage) => {
        const id = Date.now().toString();
        const newChat: Chat = {
          id,
          backendId,
          title,
          createdAt: new Date(),
          updatedAt: new Date(),
          messages: [
            {
              id: Date.now().toString(),
              role: "user",
              content: firstMessage,
              timestamp: new Date(),
            },
          ],
        };
        set((state) => ({ chats: [newChat, ...state.chats], currentChat: newChat }));
        return id;
      },
    }),
    {
      name: "schoolai-dashboard",
      partialize: (state) => ({
        chats: state.chats,
        currentChat: state.currentChat,
        user: state.user,
      }),
    }
  )
);
