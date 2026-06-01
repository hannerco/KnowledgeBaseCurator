import { FiClock, FiFileText, FiUploadCloud } from "react-icons/fi";

import { Button } from "@/src/components/ui/Button";
import { Divider } from "@/src/components/ui/Divider";
import type { ExamResponse } from "@/src/types/exam.types";

interface ExamKeyCardProps {
  exam: ExamResponse;
  examKeyText: string | null;
  showKeyText: boolean;
  keyFileName: string;
  loadingKey: boolean;
  inputRef: React.RefObject<HTMLInputElement | null>;
  formatDate: (value?: string) => string;
  onToggleText: () => void;
  onUpload: () => void;
  onFileNameChange: (name: string) => void;
}

export function ExamKeyCard({
  exam,
  examKeyText,
  showKeyText,
  keyFileName,
  loadingKey,
  inputRef,
  formatDate,
  onToggleText,
  onUpload,
  onFileNameChange,
}: ExamKeyCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-[#1a2b4a]">{exam.title}</h2>
          {exam.description && (
            <p className="text-xs text-gray-400 mt-1">{exam.description}</p>
          )}
          <p className="text-xs text-gray-500 mt-2">
            {examKeyText ? "Clave cargada" : "Sin clave registrada"}
          </p>
        </div>
        <span className="text-[10px] text-gray-300 flex items-center gap-1">
          <FiClock className="h-3 w-3" /> {formatDate(exam.created_at)}
        </span>
      </div>

      <Divider text="Clave base" />
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-4 items-end">
        <div className="space-y-2">
          
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex-1 min-w-[220px] h-10 flex items-center gap-3 border border-gray-200 bg-white rounded-xl px-4 text-xs text-gray-500 cursor-pointer hover:border-blue-200 hover:bg-blue-50/40 transition">
              <FiFileText className="h-4 w-4 text-gray-400" />
              <span className="truncate">
                {keyFileName || "Elegir PDF base"}
              </span>
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf"
                onChange={(e) => onFileNameChange(e.target.files?.[0]?.name ?? "")}
                className="hidden"
              />
            </label>
            <Button className="w-auto px-3 text-xs h-10" isLoading={loadingKey} onClick={onUpload}>
              <span className="inline-flex items-center gap-2">
                <FiUploadCloud className="h-4 w-4" /> Subir
              </span>
            </Button>
          </div>
        </div>
        <button
          onClick={onToggleText}
          className="self-start md:self-center text-xs text-blue-700 hover:text-blue-900 border border-blue-100 px-3 py-2 rounded-lg bg-blue-50/60"
          disabled={loadingKey}
        >
          {showKeyText ? "Ocultar texto" : "Ver texto extraido"}
        </button>
      </div>
      {showKeyText && examKeyText && (
        <div className="mt-3 bg-gray-50 border border-gray-100 rounded-xl p-4 text-[12px] text-gray-600 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
          {examKeyText}
        </div>
      )}
    </div>
  );
}
