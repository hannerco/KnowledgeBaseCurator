"use client";

import { useParams } from "next/navigation";
import { useDashboardStore } from "@/src/store/dashboard.store";
import { useAuthStore } from "@/src/store/auth.store";
import { ChatInput } from "@/src/components/dashboard/chat/ChatInput";
import { apiSendMessage, apiGetMessages } from "@/src/services/chat.service";
import { useEffect, useRef, useCallback, useState } from "react";
import { RiGraduationCapLine, RiGlobalLine } from "react-icons/ri";
import { HiOutlineDocumentText } from "react-icons/hi2";
import { SelectedSources } from "@/src/components/dashboard/chat/SourcesModal";
import { MessageContent } from "@/src/app/dashboard/chat/[id]/MessageContent";

export default function ChatPage() {
  const params = useParams();
  const localId = params.id as string;

  const chat = useDashboardStore((s) => s.chats.find((c) => c.id === localId));
  const updateChat = useDashboardStore((s) => s.updateChat);
  const addAgentMessage = useDashboardStore((s) => s.addAgentMessage);
  const setAgentTyping = useDashboardStore((s) => s.setAgentTyping);
  const isAgentTyping = useDashboardStore((s) => s.isAgentTyping);
  const token = useAuthStore((s) => s.token);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [activeSources, setActiveSources] = useState<SelectedSources>({
    globalIds: [],
    localFilenames: [],
  });

  useEffect(() => {
    if (!chat || !token || chat.messages.length > 0) return;
    apiGetMessages(token, chat.backendId)
      .then((msgs) => {
        const mapped = msgs.map((m) => ({
          id: m.id.toString(),
          role: m.sender as "user" | "assistant",
          content: m.content,
          timestamp: new Date(m.timestamp),
        }));
        updateChat(localId, { messages: mapped });
      })
      .catch(console.error);
  }, [chat?.backendId, token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages, isAgentTyping]);

  const handleSendMessage = useCallback(
    async (message: string, sources?: SelectedSources) => {
      if (!message.trim() || !chat || isAgentTyping) return;

      if (sources) setActiveSources(sources);

      const finalSources = sources ?? activeSources;

      const userMessage = {
        id: Date.now().toString(),
        role: "user" as const,
        content: message,
        timestamp: new Date(),
        sources:
          finalSources.localFilenames.length > 0 ||
          finalSources.globalIds.length > 0
            ? finalSources
            : undefined,
      };

      updateChat(localId, {
        messages: [...chat.messages, userMessage],
        updatedAt: new Date(),
      });
      setAgentTyping(true);

      try {
        const currentToken =
          token ??
          (typeof window !== "undefined"
            ? localStorage.getItem("authToken")
            : "");
        if (!currentToken) {
          addAgentMessage(
            localId,
            "Error: No se encontró un token válido. Inicia sesión de nuevo.",
          );
          return;
        }

        const pair = await apiSendMessage(
          currentToken,
          chat.backendId,
          message,
          finalSources.localFilenames.length > 0
            ? finalSources.localFilenames
            : undefined,
          finalSources.globalIds.length > 0
            ? finalSources.globalIds
            : undefined,
        );
        addAgentMessage(localId, pair.assistant_message.content);
      } catch {
        addAgentMessage(
          localId,
          "Lo siento, hubo un error al procesar tu mensaje. Intenta de nuevo.",
        );
      }
    },
    [
      token,
      chat,
      isAgentTyping,
      updateChat,
      localId,
      setAgentTyping,
      addAgentMessage,
      activeSources,
    ],
  );

  if (!chat) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#f0f5ff]">
        <p className="text-gray-400 text-sm">Chat no encontrado</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-[#f0f5ff]">
      <div className="flex-1 overflow-y-auto px-3 md:px-6 py-4 md:py-6">
        <div className="space-y-4 md:space-y-5 max-w-3xl mx-auto">
          {chat.messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-end gap-2 md:gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-6 h-6 md:w-7 md:h-7 rounded-full bg-blue-950 flex items-center justify-center shrink-0 mb-0.5">
                  <RiGraduationCapLine className="h-3 w-3 md:h-3.5 md:w-3.5 text-white" />
                </div>
              )}
              <div
                className={`max-w-[85%] md:max-w-[72%] rounded-2xl px-3 py-2.5 md:px-4 md:py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-[#1a2b4a] text-white rounded-br-sm shadow-md"
                    : "bg-white border border-gray-100 text-gray-800 rounded-bl-sm shadow-sm"
                }`}
              >
                {msg.role === "assistant" ? (
                  <>
                    {console.log("RAW:", msg.content)}
                    <MessageContent content={msg.content} />
                  </>
                ) : (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}

                {msg.role === "user" &&
                  msg.sources &&
                  (msg.sources.localFilenames.length > 0 ||
                    msg.sources.globalIds.length > 0) && (
                    <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-white/20">
                      {msg.sources.localFilenames.map((filename) => (
                        <span
                          key={filename}
                          className="flex items-center gap-1 text-[10px] font-medium bg-white/15 text-white/80 px-2 py-0.5 rounded-full"
                        >
                          <HiOutlineDocumentText className="h-3 w-3 shrink-0" />
                          {filename}
                        </span>
                      ))}
                      {msg.sources.globalIds.map((id) => (
                        <span
                          key={id}
                          className="flex items-center gap-1 text-[10px] font-medium bg-white/15 text-white/80 px-2 py-0.5 rounded-full"
                        >
                          <RiGlobalLine className="h-3 w-3 shrink-0" />
                          Global
                        </span>
                      ))}
                    </div>
                  )}
              </div>
            </div>
          ))}

          {isAgentTyping && (
            <div className="flex items-end gap-2 md:gap-3">
              <div className="w-6 h-6 md:w-7 md:h-7 rounded-full bg-blue-950 flex items-center justify-center shrink-0">
                <RiGraduationCapLine className="h-3 w-3 md:h-3.5 md:w-3.5 text-white" />
              </div>
              <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 bg-blue-950 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 bg-blue-950 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 bg-blue-950 rounded-full animate-bounce" />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-gray-100 px-3 md:px-6 pt-3 pb-4 md:pb-8 bg-[#f0f5ff]">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSend={handleSendMessage}
            disabled={isAgentTyping}
            placeholder={
              isAgentTyping
                ? "SchoolAI está respondiendo..."
                : "Pregunta a SchoolAI..."
            }
            chatId={chat.backendId}
            token={token ?? ""}
          />
        </div>
      </div>
    </div>
  );
}
