"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useDashboardStore } from "@/src/store/dashboard.store";
import { useAuthStore } from "@/src/store/auth.store";
import { ChatInput } from "@/src/components/dashboard/chat/ChatInput";
import { apiCreateChat, apiSendMessage } from "@/src/services/chat.service";
import {
  apiGetUserDocuments,
  apiUploadUserDocument,
  apiDeleteDocument,
  DocumentResponse,
} from "@/src/services/document.service";
import { useLoadChats } from "@/src/hooks/useLoadChats";
import {
  RiSparklingLine,
  RiFileHistoryLine,
  RiChatSmile3Line,
  RiUploadCloudLine,
  RiDeleteBinLine,
  RiFilePdfLine,
} from "react-icons/ri";

const SUGGESTIONS = [
  "Crea un plan de estudio para matemáticas",
  "Revisa mi taller de arquitectura",
  "Explícame la técnica Pomodoro",
  "Genera un resumen de mis apuntes",
];

export default function Dashboard() {
  const router = useRouter();
  const addChatFromBackend = useDashboardStore((state) => state.addChatFromBackend);
  const addAgentMessage = useDashboardStore((state) => state.addAgentMessage);
  const setAgentTyping = useDashboardStore((state) => state.setAgentTyping);
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);

  const [activeTab, setActiveTab] = useState<"docs" | "chats">("docs");
  const [userDocs, setUserDocs] = useState<DocumentResponse[]>([]);
  const [uploadingUser, setUploadingUser] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialLoadDone, setInitialLoadDone] = useState(false);

  useLoadChats();

  useEffect(() => {
    const currentToken = useAuthStore.getState().token;
    if (!currentToken || initialLoadDone) return;

    apiGetUserDocuments(currentToken)
      .then(setUserDocs)
      .catch((err) => console.error("Error loading user docs:", err));

    setInitialLoadDone(true);
  }, [initialLoadDone]);

  const reloadDocuments = useCallback(async () => {
    const currentToken = useAuthStore.getState().token;
    if (!currentToken) return;
    try {
      const userDocsData = await apiGetUserDocuments(currentToken);
      setUserDocs(userDocsData);
    } catch (err) {
      console.error("Error loading documents:", err);
    }
  }, []);

  const handleUploadUser = async (file: File) => {
    const currentToken = useAuthStore.getState().token;
    if (!currentToken) return;
    setUploadingUser(true);
    setError(null);
    try {
      await apiUploadUserDocument(currentToken, file);
      await reloadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir");
    } finally {
      setUploadingUser(false);
    }
  };

  const handleDeleteDocument = async (docId: number) => {
    const currentToken = useAuthStore.getState().token;
    if (!currentToken) return;
    try {
      await apiDeleteDocument(currentToken, docId);
      await reloadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const handleSendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;
    try {
      const currentToken = token || (typeof window !== "undefined" ? localStorage.getItem("authToken") : "");
      if (!currentToken) {
        console.warn("No hay token disponible para enviar el mensaje");
        return;
      }

      const backendChat = await apiCreateChat(currentToken, message.slice(0, 40));
      const localId = addChatFromBackend(backendChat.id, backendChat.title, message);
      router.push(`/dashboard/chat/${localId}`);
      setAgentTyping(true);
      const pair = await apiSendMessage(currentToken, backendChat.id, message);
      addAgentMessage(localId, pair.assistant_message.content);
    } catch (err) {
      console.error("Error:", err);
    }
  }, [token, addChatFromBackend, router, setAgentTyping, addAgentMessage]);

  const firstName = user?.name?.split(" ")[0] ?? "Profesor";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Buenos días" : hour < 18 ? "Buenas tardes" : "Buenas noches";

  return (
      <div className="min-h-screen bg-[#f0f5ff] overflow-x-hidden">
        <div className="flex items-center justify-end px-8 py-10" />

        <div className="flex justify-center px-6 pb-16">
          <div className="w-full max-w-6xl">
            
            <div className="flex flex-col items-center text-center mb-12 pt-8">
              <div className="flex items-center gap-2 mb-2">
                <RiSparklingLine className="h-5 w-5 text-blue-500" />

                <p
                  className="text-sm font-medium text-blue-500"
                  suppressHydrationWarning
                >
                  {greeting}
                </p>
              </div>

              <h1
                className="text-3xl font-bold text-[#1a2b4a] mb-2 tracking-tight"
                suppressHydrationWarning
              >
                {firstName}, ¿en qué trabajamos hoy?
              </h1>

              <p className="text-gray-400 text-sm max-w-xl">
                Sube documentos personales o inicia un nuevo chat con SchoolAI.
              </p>
            </div>

        {activeTab === "docs" && (
          <div className="mt-8 flex flex-col items-center">
            <div className="w-full max-w-2xl mb-8">
              <ChatInput onSend={handleSendMessage} chatId={0} token={token ?? ""} />
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSendMessage(s)}
                  className="text-xs font-medium text-blue-700 bg-blue-50 border border-blue-100 hover:bg-blue-100 hover:border-blue-200 px-4 py-2 rounded-full transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
            )}
          </div>
        </div>
      </div>
  
  );
}