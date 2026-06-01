import { FiCheckCircle, FiLoader } from "react-icons/fi";

import type { ExamResponse } from "@/src/types/exam.types";

interface ExamListCardProps {
  exams: ExamResponse[];
  selectedExamId: number | null;
  loading: boolean;
  formatDate: (value?: string) => string;
  onSelect: (examId: number) => void;
}

export function ExamListCard({
  exams,
  selectedExamId,
  loading,
  formatDate,
  onSelect,
}: ExamListCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-[#1a2b4a]">Mis examenes</h2>
        {loading && <FiLoader className="h-4 w-4 animate-spin text-gray-400" />}
      </div>
      <div className="space-y-2">
        {exams.length === 0 && (
          <div className="border border-dashed border-gray-200 rounded-xl px-4 py-6 text-center text-xs text-gray-400">
            Aun no tienes examenes.
          </div>
        )}
        {exams.map((exam) => {
          const isActive = exam.id === selectedExamId;
          return (
            <button
              key={exam.id}
              onClick={() => onSelect(exam.id)}
              className={`w-full text-left rounded-xl border px-3 py-2 transition ${
                isActive
                  ? "border-blue-200 bg-blue-50"
                  : "border-gray-200 hover:border-blue-100 hover:bg-blue-50/40"
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-[#1a2b4a] truncate">{exam.title}</p>
                {isActive && <FiCheckCircle className="h-4 w-4 text-blue-600" />}
              </div>
              {exam.description && (
                <p className="text-[11px] text-gray-400 mt-1 line-clamp-2">
                  {exam.description}
                </p>
              )}
              <p className="text-[10px] text-gray-300 mt-2">
                Creado {formatDate(exam.created_at)}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
