"use client";

import { useState, useEffect, useCallback } from "react";
import { FiX, FiLoader } from "react-icons/fi";
import { HiOutlineDocumentText } from "react-icons/hi2";
import { RiGlobalLine } from "react-icons/ri";
import { apiGetGlobalDocuments, GlobalDocument } from "@/src/services/document.service";

interface GlobalFilesModalProps {
  isOpen: boolean;
  onClose: () => void;
  token: string;
  selectedIds: string[];
  onConfirm: (ids: string[]) => void;
}

export function GlobalFilesModal({ isOpen, onClose, token, selectedIds, onConfirm }: GlobalFilesModalProps) {
  const [globalDocs, setGlobalDocs] = useState<GlobalDocument[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setSelected(new Set(selectedIds));
    setLoading(true);
    apiGetGlobalDocuments(token)
      .then(setGlobalDocs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [isOpen]);

  const toggle = (id: string) => setSelected((prev) => {
    const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n;
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white w-full sm:max-w-lg flex flex-col overflow-hidden rounded-t-2xl sm:rounded-2xl shadow-2xl max-h-[90vh] sm:max-h-[80vh]">

        <div className="flex items-center justify-between px-4 md:px-6 py-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-bold text-[#1a2b4a]">Archivos globales</h2>
            <p className="text-xs text-gray-400 mt-0.5">Selecciona documentos base como contexto</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100">
            <FiX className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading && (
            <div className="text-center py-10">
              <FiLoader className="h-6 w-6 text-gray-300 mx-auto mb-2 animate-spin" />
              <p className="text-xs text-gray-400">Cargando documentos...</p>
            </div>
          )}
          {!loading && globalDocs.length === 0 && (
            <div className="text-center py-10">
              <RiGlobalLine className="h-8 w-8 text-gray-200 mx-auto mb-2" />
              <p className="text-xs text-gray-400">No hay archivos globales aún.</p>
            </div>
          )}
          {!loading && globalDocs.map((doc) => {
            const isSelected = selected.has(doc.id);
            return (
              <button key={doc.id} onClick={() => toggle(doc.id)}
                className={`w-full flex items-center gap-3 px-3 md:px-4 py-3 rounded-xl border transition-all text-left ${isSelected ? "border-[#1a2b4a] bg-[#f0f5ff]" : "border-gray-100 hover:border-gray-200 hover:bg-gray-50"}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isSelected ? "bg-[#1a2b4a]" : "bg-red-50"}`}>
                  <HiOutlineDocumentText className={`h-4 w-4 ${isSelected ? "text-white" : "text-red-400"}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-700 truncate">{doc.filename}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">{doc.chunks_indexed} fragmentos</p>
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