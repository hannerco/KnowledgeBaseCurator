import { FiFileText, FiLoader, FiUploadCloud } from "react-icons/fi";

import { Button } from "@/src/components/ui/Button";
import { Divider } from "@/src/components/ui/Divider";
import { Input } from "@/src/components/ui/Input";
import type { ExamSubmissionResponse } from "@/src/types/exam.types";

interface ExamSubmissionsCardProps {
  studentName: string;
  onStudentNameChange: (value: string) => void;
  submissionFileName: string;
  onFileNameChange: (name: string) => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onUpload: () => void;
  submissions: ExamSubmissionResponse[];
  selectedSubmissionId: number | null;
  loading: boolean;
  formatDate: (value?: string) => string;
  onSelect: (submissionId: number) => void;
}

export function ExamSubmissionsCard({
  studentName,
  onStudentNameChange,
  submissionFileName,
  onFileNameChange,
  inputRef,
  onUpload,
  submissions,
  selectedSubmissionId,
  loading,
  formatDate,
  onSelect,
}: ExamSubmissionsCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
      <Divider text="Submissions" />
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-4 items-end">
        <div className="space-y-3">
          <Input
            label="Nombre del estudiante"
            placeholder="Opcional"
            value={studentName}
            onChange={(e) => onStudentNameChange(e.target.value)}
          />
          <label className="h-10 flex items-center gap-3 border border-gray-200 bg-white rounded-xl px-4 text-xs text-gray-500 cursor-pointer hover:border-blue-200 hover:bg-blue-50/40 transition">
            <FiFileText className="h-4 w-4 text-gray-400" />
            <span className="truncate">
              {submissionFileName || "Elegir PDF del estudiante"}
            </span>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              onChange={(e) => onFileNameChange(e.target.files?.[0]?.name ?? "")}
              className="hidden"
            />
          </label>
        </div>
        <Button className="w-auto px-3 text-xs h-10" isLoading={loading} onClick={onUpload}>
          <span className="inline-flex items-center gap-2">
            <FiUploadCloud className="h-4 w-4" /> Subir
          </span>
        </Button>
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-[#1a2b4a]">Listado</h3>
          {loading && <FiLoader className="h-4 w-4 animate-spin text-gray-400" />}
        </div>
        <div className="space-y-2">
          {submissions.length === 0 && (
            <div className="border border-dashed border-gray-200 rounded-xl px-4 py-6 text-center text-xs text-gray-400">
              No hay submissions aun.
            </div>
          )}
          {submissions.map((submission) => {
            const isActive = submission.id === selectedSubmissionId;
            return (
              <button
                key={submission.id}
                onClick={() => onSelect(submission.id)}
                className={`w-full text-left border rounded-xl px-3 py-2 transition ${
                  isActive
                    ? "border-blue-200 bg-blue-50"
                    : "border-gray-200 hover:border-blue-100 hover:bg-blue-50/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FiFileText className="h-4 w-4 text-gray-400" />
                    <p className="text-xs font-semibold text-[#1a2b4a]">
                      {submission.student_name || submission.filename}
                    </p>
                  </div>
                  <span className="text-[10px] text-gray-300">{formatDate(submission.created_at)}</span>
                </div>
                <p className="text-[11px] text-gray-400 mt-1">
                  {submission.filename} · {submission.answers_count} respuestas
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
