"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { FiX, FiUploadCloud, FiCheckCircle, FiLoader } from "react-icons/fi";
import { HiOutlineDocumentText } from "react-icons/hi2";
import { apiGetUserDocuments, apiUploadUserDocument } from "@/src/services/document.service";

interface LocalFilesModalProps {
  isOpen: boolean;
  onClose: () => void;
  token: string;
  selectedFilenames: string[];
  onConfirm: (filenames: string[]) => void;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "short" });
}

type UploadStatus = "uploading" | "success" | "error";
interface PendingUpload { file: File; status: UploadStatus; error?: string; }
interface LocalDoc { id: number; filename: string; uploaded_at: string; }

export function LocalFilesModal({ isOpen, onClose, token, selectedFilenames, onConfirm }: LocalFilesModalProps) {
  const [localDocs, setLocalDocs] = useState<LocalDoc[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [pendingUploads, setPendingUploads] = useState<PendingUpload[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocs = useCallback(async () => {
    const docs = await apiGetUserDocuments(token);
    const userOnly = docs.filter((d) => d.document_type === "user_upload");
    setLocalDocs(userOnly.map((d) => ({ id: d.id, filename: d.filename, uploaded_at: d.uploaded_at })));
  }, [token]);

  useEffect(() => {
    if (!isOpen) return;
    setSelected(new Set(selectedFilenames));
    setPendingUploads([]);
    loadDocs();
  }, [isOpen]);

  const toggle = (filename: string) => setSelected((prev) => {
    const n = new Set(prev); n.has(filename) ? n.delete(filename) : n.add(filename); return n;
  });

  const handleUpload = useCallback(async (file: File) => {
    if (file.type !== "application/pdf") {
      setPendingUploads((prev) => [...prev, { file, status: "error", error: "Solo PDFs" }]);
      return;
    }
    setPendingUploads((prev) => [...prev, { file, status: "uploading" }]);
    try {
      await apiUploadUserDocument(token, file);
      await loadDocs();
      setSelected((prev) => new Set([...prev, file.name]));
      setPendingUploads((prev) => prev.map((p) => p.file === file ? { ...p, status: "success" } : p));
    } catch (err) {
      setPendingUploads((prev) => prev.map((p) =>
        p.file === file ? { ...p, status: "error", error: err instanceof Error ? err.message : "Error" } : p
      ));
    }
  }, [token, loadDocs]);

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach(handleUpload);
  }, [handleUpload]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white w-full sm:max-w-lg flex flex-col overflow-hidden rounded-t-2xl sm:rounded-2xl shadow-2xl max-h-[90vh] sm:max-h-[80vh]">

        <div className="flex items-center justify-between px-4 md:px-6 py-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-bold text-[#1a2b4a]">Archivos de este chat</h2>
            <p className="text-xs text-gray-400 mt-0.5">Sube o selecciona documentos para usar como contexto</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100">
            <FiX className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <div
            onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFiles(e.dataTransfer.files); }}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => fileInputRef.current?.click()}
            className={`rounded-xl border-2 border-dashed p-5 flex flex-col items-center justify-center cursor-pointer transition-colors ${isDragging ? "border-blue-400 bg-blue-50" : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/40"}`}
          >
            <input ref={fileInputRef} type="file" accept=".pdf" multiple className="hidden" onChange={(e) => handleFiles(e.target.files)} />
            <FiUploadCloud className="h-6 w-6 text-gray-300 mb-2" />
            <p className="text-xs font-semibold text-gray-500">Arrastra un PDF o haz clic</p>
            <p className="text-[10px] text-gray-400 mt-0.5">Max 50MB</p>
          </div>

          {pendingUploads.map((u, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-100 bg-gray-50">
              <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center shrink-0">
                <HiOutlineDocumentText className="h-4 w-4 text-red-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-gray-700 truncate">{u.file.name}</p>
              </div>
              {u.status === "uploading" && <span className="flex items-center gap-1 text-[10px] text-blue-500 font-medium shrink-0"><FiLoader className="h-3 w-3 animate-spin" />Subiendo...</span>}
              {u.status === "success" && <FiCheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />}
              {u.status === "error" && <span className="text-[10px] text-red-500 shrink-0">{u.error}</span>}
            </div>
          ))}

          {localDocs.length === 0 && pendingUploads.length === 0 && (
            <p className="text-center text-xs text-gray-400 py-4">Aún no has subido archivos en este chat</p>
          )}

          {localDocs.map((doc) => {
            const isSelected = selected.has(doc.filename);
            return (
              <button key={doc.id} onClick={() => toggle(doc.filename)}
                className={`w-full flex items-center gap-3 px-3 md:px-4 py-3 rounded-xl border transition-all text-left ${isSelected ? "border-[#1a2b4a] bg-[#f0f5ff]" : "border-gray-100 hover:border-gray-200 hover:bg-gray-50"}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isSelected ? "bg-[#1a2b4a]" : "bg-red-50"}`}>
                  <HiOutlineDocumentText className={`h-4 w-4 ${isSelected ? "text-white" : "text-red-400"}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-700 truncate">{doc.filename}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">{formatDate(doc.uploaded_at)}</p>
                </div>
                <div className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${isSelected ? "border-[#1a2b4a] bg-[#1a2b4a]" : "border-gray-300"}`}>
                  {isSelected && <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 12 12"><path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>}
                </div>
              </button>
            );
          })}
        </div>

        <div className="border-t border-gray-100 px-4 md:px-6 py-4 flex items-center justify-between">
          <p className="text-xs text-gray-400">
            {selected.size === 0 ? "Sin archivos seleccionados" : `${selected.size} archivo${selected.size !== 1 ? "s" : ""} seleccionado${selected.size !== 1 ? "s" : ""}`}
          </p>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-3 md:px-4 py-2 text-xs font-semibold text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">Cancelar</button>
            <button onClick={() => { onConfirm(Array.from(selected)); onClose(); }} className="px-3 md:px-4 py-2 text-xs font-semibold text-white bg-[#1a2b4a] hover:bg-blue-900 rounded-lg transition-colors">Confirmar</button>
          </div>
        </div>
      </div>
    </div>
  );
}