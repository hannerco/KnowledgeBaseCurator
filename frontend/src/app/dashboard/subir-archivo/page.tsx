"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import {
  FiUploadCloud,
  FiCheckCircle,
  FiXCircle,
  FiLoader,
} from "react-icons/fi";
import { HiOutlineDocumentText } from "react-icons/hi2";
import { RiGlobalLine } from "react-icons/ri";

import { useAuthStore } from "@/src/store/auth.store";
import { useGlobalDocsStore } from "@/src/store/global-docs.store";

import {
  apiUploadGlobalDocument,
  apiGetGlobalDocuments,
  GlobalDocument,
} from "@/src/services/document.service";

type UploadStatus = "idle" | "uploading" | "success" | "error";

interface UploadedFile {
  name: string;
  size: number;
  status: UploadStatus;
  chunks?: number;
  error?: string;
}

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function SubirArchivoPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [globalDocs, setGlobalDocs] = useState<GlobalDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);

  const inputRef = useRef<HTMLInputElement>(null);

  const token = useAuthStore((state) => state.token);

  const selectedGlobalDocs = useGlobalDocsStore(
    (state) => state.selectedGlobalDocs
  );

  const toggleGlobalDoc = useGlobalDocsStore(
    (state) => state.toggleGlobalDoc
  );

  useEffect(() => {
    const activeToken =
      token ||
      (typeof window !== "undefined"
        ? localStorage.getItem("authToken")
        : "");

    if (!activeToken) return;

    setLoadingDocs(true);

    apiGetGlobalDocuments(activeToken)
      .then(setGlobalDocs)
      .catch((err) =>
        console.error("Error loading global docs:", err)
      )
      .finally(() => setLoadingDocs(false));
  }, [token]);

  const reloadGlobalDocs = useCallback(async () => {
    const activeToken =
      token ||
      (typeof window !== "undefined"
        ? localStorage.getItem("authToken")
        : "");

    if (!activeToken) return;

    try {
      const docs = await apiGetGlobalDocuments(activeToken);
      setGlobalDocs(docs);
    } catch (err) {
      console.error("Error reloading global docs:", err);
    }
  }, [token]);

  const uploadFile = useCallback(
    async (file: File) => {
      setFiles((prev) => [
        ...prev,
        {
          name: file.name,
          size: file.size,
          status: "uploading",
        },
      ]);

      try {
        const activeToken =
          token ||
          (typeof window !== "undefined"
            ? localStorage.getItem("authToken")
            : "");

        if (!activeToken) {
          throw new Error("No hay sesión activa");
        }

        const data = await apiUploadGlobalDocument(
          activeToken,
          file
        );

        setFiles((prev) =>
          prev.map((f) =>
            f.name === file.name
              ? {
                  ...f,
                  status: "success",
                  chunks: data.chunks_indexed,
                }
              : f
          )
        );

        await reloadGlobalDocs();
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Error desconocido";

        setFiles((prev) =>
          prev.map((f) =>
            f.name === file.name
              ? {
                  ...f,
                  status: "error",
                  error: message,
                }
              : f
          )
        );
      }
    },
    [token, reloadGlobalDocs]
  );

  const handleFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) return;

      Array.from(incoming).forEach((file) => {
        if (file.type === "application/pdf") {
          uploadFile(file);
        } else {
          setFiles((prev) => [
            ...prev,
            {
              name: file.name,
              size: file.size,
              status: "error",
              error: "Solo se aceptan archivos PDF",
            },
          ]);
        }
      });
    },
    [uploadFile]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();

      setIsDragging(false);

      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const removeFile = (name: string) => {
    setFiles((prev) =>
      prev.filter((f) => f.name !== name)
    );
  };

  return (
    <div className="min-h-screen bg-[#f0f5ff] p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[#1a2b4a]">
            Subir archivos
          </h1>

          <p className="text-sm text-gray-400 mt-1">
            Sube documentos PDF para que SchoolAI
            los use como contexto global.
          </p>
        </div>

        <div className="flex gap-6">
          <div className="flex-1 space-y-5">
            <div
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onClick={() => inputRef.current?.click()}
              className={`rounded-2xl border-2 border-dashed p-12 flex flex-col items-center justify-center text-center transition-colors cursor-pointer bg-white ${
                isDragging
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/40"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf"
                multiple
                className="hidden"
                onChange={(e) =>
                  handleFiles(e.target.files)
                }
              />

              <div className="w-14 h-14 rounded-2xl bg-indigo-100 flex items-center justify-center mb-4">
                <FiUploadCloud className="h-7 w-7 text-indigo-500" />
              </div>

              <p className="text-base font-semibold text-[#1a2b4a] mb-1">
                Arrastra archivos académicos
              </p>

              <p className="text-sm text-gray-400 mb-6">
                PDF (Max 50MB)
              </p>

              <button
                className="bg-[#1a2b4a] text-white text-sm font-semibold px-6 py-2.5 rounded-xl hover:bg-blue-900 transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  inputRef.current?.click();
                }}
              >
                Seleccionar archivo
              </button>
            </div>


            {files.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm divide-y divide-gray-50">
                <div className="px-5 py-3 flex items-center justify-between">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Subidos en esta sesión
                  </p>

                  <button
                    onClick={() => setFiles([])}
                    className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    Limpiar
                  </button>
                </div>

                {files.map((f) => (
                  <div
                    key={f.name}
                    className="px-5 py-3.5 flex items-center gap-4"
                  >
                    <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center shrink-0">
                      <HiOutlineDocumentText className="h-5 w-5 text-red-400" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-700 truncate">
                        {f.name}
                      </p>

                      <p className="text-xs text-gray-400">
                        {formatSize(f.size)}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {f.status === "uploading" && (
                        <span className="flex items-center gap-1.5 text-xs text-blue-500 font-medium">
                          <FiLoader className="h-3.5 w-3.5 animate-spin" />
                          Indexando...
                        </span>
                      )}

                      {f.status === "success" && (
                        <span className="flex items-center gap-1.5 text-xs text-emerald-500 font-medium">
                          <FiCheckCircle className="h-3.5 w-3.5" />

                          {f.chunks
                            ? `${f.chunks} fragmentos`
                            : "Listo"}
                        </span>
                      )}

                      {f.status === "error" && (
                        <span className="flex items-center gap-1.5 text-xs text-red-500 font-medium">
                          <FiXCircle className="h-3.5 w-3.5" />

                          {f.error ?? "Error"}
                        </span>
                      )}

                      <button
                        onClick={() =>
                          removeFile(f.name)
                        }
                        className="ml-2 text-gray-300 hover:text-gray-500 transition-colors text-lg leading-none"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}



            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
              <div className="px-5 py-4 flex items-center gap-2 border-b border-gray-50">
                <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center">
                  <RiGlobalLine className="h-3.5 w-3.5 text-indigo-600" />
                </div>

                <div>
                  <p className="text-sm font-semibold text-[#1a2b4a]">
                    Fuentes globales indexadas
                  </p>

                  <p className="text-xs text-gray-400">
                    Selecciona cuáles usar en el chat
                  </p>
                </div>
              </div>

              {loadingDocs ? (
                <div className="flex items-center justify-center gap-2 py-10">
                  <FiLoader className="h-4 w-4 text-gray-300 animate-spin" />

                  <span className="text-xs text-gray-400">
                    Cargando documentos...
                  </span>
                </div>
              ) : globalDocs.length === 0 ? (
                <div className="text-center py-10">
                  <RiGlobalLine className="h-8 w-8 text-gray-200 mx-auto mb-2" />

                  <p className="text-xs text-gray-400">
                    No hay fuentes globales aún.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-50">
                  {globalDocs.map((doc) => {
                    const selected =
                      selectedGlobalDocs.includes(
                        doc.id
                      );

                    return (
                      <button
                        key={doc.id}
                        onClick={() =>
                          toggleGlobalDoc(doc.id)
                        }
                        className={`w-full px-5 py-3.5 flex items-center gap-4 transition-all text-left ${
                          selected
                            ? "bg-blue-50 border-l-4 border-blue-500"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center shrink-0">
                          <HiOutlineDocumentText className="h-5 w-5 text-red-400" />
                        </div>

                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-700 truncate">
                            {doc.filename}
                          </p>

                          <p className="text-xs text-gray-400">
                            {doc.chunks_indexed} fragmentos
                          </p>
                        </div>

                        {selected && (
                          <span className="text-[10px] font-semibold bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">
                            USANDO
                          </span>
                        )}

                        <span className="text-[10px] font-semibold bg-indigo-50 text-indigo-500 px-2 py-0.5 rounded-full">
                          GLOBAL
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>



          <div className="w-64 shrink-0 space-y-4">
            <div className="bg-[#1a2b4a] rounded-2xl p-5 text-white">
              <p className="text-xs font-semibold uppercase tracking-widest text-blue-300 mb-3">
                Formatos aceptados
              </p>

              <div className="flex items-center gap-3">
                <span className="bg-red-400 text-white text-[10px] font-bold px-2 py-0.5 rounded">
                  PDF
                </span>

                <span className="text-xs text-blue-200">
                  Documentos de texto
                </span>
              </div>

              <div className="mt-5 pt-4 border-t border-white/10">
                <p className="text-xs text-blue-200 leading-relaxed">
                  Los documentos se indexan
                  automáticamente como fuentes
                  globales y podrás elegir cuáles
                  usar en el chat.
                </p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Límites
              </p>

              <div className="space-y-2 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>Tamaño máximo</span>

                  <span className="font-semibold text-gray-700">
                    50 MB
                  </span>
                </div>

                <div className="flex justify-between">
                  <span>Formato</span>

                  <span className="font-semibold text-gray-700">
                    PDF
                  </span>
                </div>

                <div className="flex justify-between">
                  <span>PDFs escaneados</span>

                  <span className="font-semibold text-red-400">
                    No soportado
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}