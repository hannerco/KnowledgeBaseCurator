"use client";

import { useEffect, useState, useRef } from "react";
import { FiPaperclip, FiSend } from "react-icons/fi";
import { HiOutlineDocumentText } from "react-icons/hi2";
import { RiStackLine, RiGlobalLine } from "react-icons/ri";
import { LocalFilesModal } from "./LocalFilesModal";
import { GlobalFilesModal } from "./GlobalFilesModal";

export interface SelectedSources {
  globalIds: string[];
  localFilenames: string[];
}

interface ChatInputProps {
  onSend: (message: string, sources: SelectedSources) => void;
  placeholder?: string;
  disabled?: boolean;
  chatId: number;
  token: string;
}

export function ChatInput({ onSend, placeholder = "Pregunta a SchoolAI...", disabled = false, chatId, token }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [localOpen, setLocalOpen] = useState(false);
  const [globalOpen, setGlobalOpen] = useState(false);
  const [localFilenames, setLocalFilenames] = useState<string[]>([]);
  const [globalIds, setGlobalIds] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSend = () => {
    if (!message.trim() || disabled) return;
    onSend(message, { globalIds, localFilenames });
    setMessage("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const totalSources = globalIds.length + localFilenames.length;

  return (
    <>
      <LocalFilesModal
        isOpen={localOpen}
        onClose={() => setLocalOpen(false)}
        token={token}
        selectedFilenames={localFilenames}
        onConfirm={setLocalFilenames}
      />

      <GlobalFilesModal
        isOpen={globalOpen}
        onClose={() => setGlobalOpen(false)}
        token={token}
        selectedIds={globalIds}
        onConfirm={setGlobalIds}
      />

      <div className="w-full max-w-3xl mx-auto">

        {totalSources > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2 px-1">
            {localFilenames.map((filename) => (
              <div key={filename} className="flex items-center gap-1.5 bg-[#1a2b4a] text-white rounded-lg px-2.5 py-1.5 text-xs shadow-sm">
                <HiOutlineDocumentText className="h-3.5 w-3.5 shrink-0 text-blue-300" />
                <span className="max-w-[160px] truncate font-medium">{filename}</span>
                <button onClick={() => setLocalFilenames((prev) => prev.filter((f) => f !== filename))}
                  className="text-white/50 hover:text-white ml-0.5 text-sm leading-none">×</button>
              </div>
            ))}
            {globalIds.length > 0 && (
              <div className="flex items-center gap-1.5 bg-indigo-50 border border-indigo-100 text-indigo-700 rounded-lg px-2.5 py-1.5 text-xs">
                <RiGlobalLine className="h-3.5 w-3.5 shrink-0" />
                <span className="font-medium">{globalIds.length} global{globalIds.length !== 1 ? "es" : ""}</span>
                <button onClick={() => setGlobalIds([])}
                  className="text-indigo-400 hover:text-indigo-700 ml-0.5 text-sm leading-none">×</button>
              </div>
            )}
          </div>
        )}

        <div className="relative flex items-end gap-2 bg-white border border-gray-300 rounded-2xl p-3 shadow-sm focus-within:ring-2 focus-within:ring-blue-950 focus-within:border-transparent">

          <button type="button" onClick={() => setLocalOpen(true)} title="Archivos de este chat"
            className={`p-1 rounded-lg transition-colors shrink-0 self-end mb-0.5 ${localFilenames.length > 0 ? "text-[#1a2b4a]" : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"}`}>
            <FiPaperclip className="h-4 w-4" />
          </button>

          <textarea ref={textareaRef} value={message} onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown} placeholder={placeholder} disabled={disabled} rows={1}
            className="flex-1 resize-none bg-transparent outline-none text-gray-800 placeholder-gray-400 text-sm min-h-[24px] max-h-[200px] overflow-y-auto self-end" />

          <button type="button" onClick={() => setGlobalOpen(true)} title="Archivos globales"
            className={`relative p-2 rounded-lg transition-colors shrink-0 self-end ${globalIds.length > 0 ? "bg-blue-50 text-[#1a2b4a] hover:bg-blue-100" : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"}`}>
            <RiStackLine className="h-4 w-4" />
            {globalIds.length > 0 && (
              <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-[#1a2b4a] text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                {globalIds.length}
              </span>
            )}
          </button>

          <button onClick={handleSend} disabled={!message.trim() || disabled}
            className="p-2 rounded-lg bg-blue-950 text-white hover:bg-blue-900 disabled:bg-gray-200 disabled:cursor-not-allowed transition-colors shrink-0 self-end">
            <FiSend className="h-4 w-4" />
          </button>
        </div>
      </div>
    </>
  );
}