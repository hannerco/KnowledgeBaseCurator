import { FiLoader } from "react-icons/fi";

import { Button } from "@/src/components/ui/Button";
import { Divider } from "@/src/components/ui/Divider";
import type {
  ExamSubmissionDetailResponse,
  ExamSubmissionResponse,
} from "@/src/types/exam.types";

interface ExamResultCardProps {
  activeSubmission: ExamSubmissionResponse | null;
  selectedSubmissionDetail: ExamSubmissionDetailResponse | null;
  submissionText: string | null;
  showSubmissionText: boolean;
  loadingDetail: boolean;
  loadingGrading: boolean;
  onToggleText: () => void;
  onGrade: () => void;
}

const verdictConfig: Record<string, { label: string; className: string; borderClass: string }> = {
  correct: {
    label: "Correcta",
    className: "bg-emerald-50 text-emerald-700 border-emerald-200",
    borderClass: "border-emerald-200",
  },
  partial: {
    label: "Parcial",
    className: "bg-amber-50 text-amber-700 border-amber-200",
    borderClass: "border-amber-200",
  },
  incorrect: {
    label: "Incorrecta",
    className: "bg-rose-50 text-rose-700 border-rose-200",
    borderClass: "border-rose-200",
  },
  unanswered: {
    label: "Sin respuesta",
    className: "bg-gray-50 text-gray-500 border-gray-200",
    borderClass: "border-gray-200",
  },
};

export function ExamResultCard({
  activeSubmission,
  selectedSubmissionDetail,
  submissionText,
  showSubmissionText,
  loadingDetail,
  loadingGrading,
  onToggleText,
  onGrade,
}: ExamResultCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
      <Divider text="Resultado" />
      {!activeSubmission ? (
        <p className="text-xs text-gray-400">Selecciona una submission para ver el resultado.</p>
      ) : (
        <>
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#1a2b4a]">
                {activeSubmission.student_name || "Submission"}
              </p>
              <p className="text-[11px] text-gray-400">{activeSubmission.filename}</p>
            </div>
            <button
              onClick={onToggleText}
              className="text-xs text-blue-700 hover:text-blue-900 border border-blue-100 px-3 py-2 rounded-lg bg-blue-50/60"
              disabled={loadingDetail}
            >
              {showSubmissionText ? "Ocultar texto" : "Ver texto extraido"}
            </button>
          </div>

          {showSubmissionText && submissionText && (
            <div className="mt-3 bg-gray-50 border border-gray-100 rounded-xl p-4 text-[12px] text-gray-600 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
              {submissionText}
            </div>
          )}

          <div className="mt-4">
            {loadingDetail ? (
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <FiLoader className="h-4 w-4 animate-spin" /> Cargando detalle
              </div>
            ) : selectedSubmissionDetail?.grade ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-blue-50 border border-blue-100 rounded-xl p-3 min-h-[88px]">
                    <p className="text-[10px] text-blue-500 uppercase tracking-widest">Nota</p>
                    <p className="text-lg font-semibold text-blue-900">
                      {selectedSubmissionDetail.grade.total_score.toFixed(2)} / {selectedSubmissionDetail.grade.max_score.toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-3 min-h-[88px]">
                    <p className="text-[10px] text-gray-400 uppercase tracking-widest">Porcentaje</p>
                    <p className="text-lg font-semibold text-[#1a2b4a]">
                      {selectedSubmissionDetail.grade.percentage.toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-xl p-3 min-h-[88px]">
                    <p className="text-[10px] text-gray-400 uppercase tracking-widest">Confianza</p>
                    <p className="text-lg font-semibold text-[#1a2b4a]">
                      {(selectedSubmissionDetail.grade.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div
                    className={`rounded-xl p-3 border min-h-[88px] ${
                      selectedSubmissionDetail.grade.needs_review
                        ? "border-amber-200 bg-amber-50"
                        : "border-emerald-200 bg-emerald-50"
                    }`}
                  >
                    <p className="text-[10px] uppercase tracking-widest text-gray-500">Estado</p>
                    <p className="text-xs font-semibold text-gray-700 mt-1">
                      {selectedSubmissionDetail.grade.needs_review ? "Provisional" : "Final"}
                    </p>
                  </div>
                </div>
                <div className="bg-gray-50 border border-gray-100 rounded-xl p-4 text-xs text-gray-600">
                  {selectedSubmissionDetail.grade.feedback}
                </div>
                {selectedSubmissionDetail.grade.question_results?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-[#1a2b4a] mb-2">Detalle por pregunta</p>
                    <div className="space-y-2">
                      {selectedSubmissionDetail.grade.question_results.map((item) => {
                        const verdictMeta = verdictConfig[item.verdict] ?? verdictConfig.incorrect;
                        return (
                          <div key={item.id} className={`border rounded-xl p-3 ${verdictMeta.borderClass}`}>
                            <div className="flex items-center justify-between">
                              <p className="text-xs font-semibold text-[#1a2b4a]">
                                Pregunta {item.question_number}
                              </p>
                              <span className="text-[11px] text-gray-400">
                                {item.score.toFixed(1)} / {item.max_score.toFixed(1)}
                              </span>
                            </div>
                            <span
                              className={`inline-flex items-center px-2 py-0.5 mt-2 text-[10px] font-semibold border rounded-full ${verdictMeta.className}`}
                            >
                              {verdictMeta.label}
                            </span>
                            <p className="text-[11px] text-gray-500 mt-1">{item.reason}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-400">Aun no esta calificada.</p>
                <Button isLoading={loadingGrading} className="w-auto px-4" onClick={onGrade}>
                  Calificar con IA
                </Button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
