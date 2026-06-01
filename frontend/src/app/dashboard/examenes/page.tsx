"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ExamCreateCard } from "@/src/components/dashboard/exams/ExamCreateCard";
import { ExamKeyCard } from "@/src/components/dashboard/exams/ExamKeyCard";
import { ExamListCard } from "@/src/components/dashboard/exams/ExamListCard";
import { ExamResultCard } from "@/src/components/dashboard/exams/ExamResultCard";
import { ExamSubmissionsCard } from "@/src/components/dashboard/exams/ExamSubmissionsCard";
import { useAuthStore } from "@/src/store/auth.store";
import { useExamStore } from "@/src/store/exam.store";
import {
  apiCreateExam,
  apiGetExamKeyText,
  apiGetExamSubmission,
  apiGetExamSubmissionText,
  apiGetExamSubmissions,
  apiGetExams,
  apiGradeSubmission,
  apiUploadExamKey,
  apiUploadExamSubmission,
} from "@/src/services/exam.service";

function formatDate(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString();
}

export default function ExamenesPage() {
  const token = useAuthStore((state) => state.token);

  const {
    exams,
    selectedExamId,
    submissions,
    selectedSubmissionId,
    selectedSubmissionDetail,
    examKeyText,
    loading,
    error,
    setExams,
    setSelectedExamId,
    setSubmissions,
    setSelectedSubmissionId,
    setSelectedSubmissionDetail,
    setExamKeyText,
    setLoading,
    setError,
  } = useExamStore();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [studentName, setStudentName] = useState("");
  const [submissionText, setSubmissionText] = useState<string | null>(null);
  const [showKeyText, setShowKeyText] = useState(false);
  const [showSubmissionText, setShowSubmissionText] = useState(false);
  const [keyFileName, setKeyFileName] = useState("");
  const [submissionFileName, setSubmissionFileName] = useState("");

  const keyInputRef = useRef<HTMLInputElement>(null);
  const submissionInputRef = useRef<HTMLInputElement>(null);

  const activeExam = useMemo(
    () => exams.find((exam) => exam.id === selectedExamId) ?? null,
    [exams, selectedExamId]
  );

  const activeSubmission = useMemo(
    () => submissions.find((item) => item.id === selectedSubmissionId) ?? null,
    [submissions, selectedSubmissionId]
  );

  const loadExams = useCallback(async () => {
    if (!token) return;
    setLoading({ exams: true });
    setError(null);
    try {
      const data = await apiGetExams(token);
      setExams(data);
      if (selectedExamId && !data.find((exam) => exam.id === selectedExamId)) {
        setSelectedExamId(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error cargando examenes");
    } finally {
      setLoading({ exams: false });
    }
  }, [token, selectedExamId, setExams, setLoading, setError, setSelectedExamId]);

  const loadKeyText = useCallback(
    async (examId: number) => {
      if (!token) return;
      setLoading({ key: true });
      try {
        const keyData = await apiGetExamKeyText(token, examId);
        setExamKeyText(keyData.raw_text);
      } catch (err) {
        const message = err instanceof Error ? err.message : "";
        if (message.toLowerCase().includes("no encontrada") || message.includes("404")) {
          setExamKeyText(null);
        } else {
          setError(message || "Error cargando clave");
        }
      } finally {
        setLoading({ key: false });
      }
    },
    [token, setLoading, setExamKeyText, setError]
  );

  const loadSubmissions = useCallback(
    async (examId: number) => {
      if (!token) return;
      setLoading({ submissions: true });
      setError(null);
      try {
        const data = await apiGetExamSubmissions(token, examId);
        setSubmissions(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error cargando submissions");
      } finally {
        setLoading({ submissions: false });
      }
    },
    [token, setLoading, setError, setSubmissions]
  );

  const loadSubmissionDetail = useCallback(
    async (examId: number, submissionId: number) => {
      if (!token) return;
      setLoading({ submissionDetail: true });
      setError(null);
      try {
        const detail = await apiGetExamSubmission(token, examId, submissionId);
        setSelectedSubmissionDetail(detail);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error cargando submission");
      } finally {
        setLoading({ submissionDetail: false });
      }
    },
    [token, setLoading, setError, setSelectedSubmissionDetail]
  );

  useEffect(() => {
    loadExams();
  }, [loadExams]);

  useEffect(() => {
    if (!selectedExamId) return;
    setSelectedSubmissionId(null);
    setSelectedSubmissionDetail(null);
    setSubmissionText(null);
    setShowSubmissionText(false);
    setShowKeyText(false);
    loadKeyText(selectedExamId);
    loadSubmissions(selectedExamId);
  }, [selectedExamId, loadKeyText, loadSubmissions, setSelectedSubmissionDetail, setSelectedSubmissionId]);

  const handleCreateExam = async () => {
    if (!token) return;
    if (!title.trim()) {
      setError("El titulo es obligatorio");
      return;
    }
    setLoading({ exams: true });
    setError(null);
    try {
      const payload = await apiCreateExam(token, {
        title: title.trim(),
        description: description.trim() || undefined,
      });
      setTitle("");
      setDescription("");
      setExams([payload, ...exams]);
      setSelectedExamId(payload.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error creando examen");
    } finally {
      setLoading({ exams: false });
    }
  };

  const handleUploadKey = async () => {
    if (!token || !selectedExamId) return;
    const file = keyInputRef.current?.files?.[0];
    if (!file) {
      setError("Selecciona un PDF base");
      return;
    }
    setLoading({ key: true });
    setError(null);
    try {
      await apiUploadExamKey(token, selectedExamId, file);
      if (keyInputRef.current) keyInputRef.current.value = "";
      setKeyFileName("");
      await loadKeyText(selectedExamId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error subiendo examen base");
    } finally {
      setLoading({ key: false });
    }
  };

  const handleUploadSubmission = async () => {
    if (!token || !selectedExamId) return;
    const file = submissionInputRef.current?.files?.[0];
    if (!file) {
      setError("Selecciona un PDF del estudiante");
      return;
    }
    setLoading({ submissions: true });
    setError(null);
    try {
      await apiUploadExamSubmission(token, selectedExamId, file, studentName.trim() || undefined);
      if (submissionInputRef.current) submissionInputRef.current.value = "";
      setSubmissionFileName("");
      setStudentName("");
      await loadSubmissions(selectedExamId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error subiendo submission");
    } finally {
      setLoading({ submissions: false });
    }
  };

  const handleSelectSubmission = async (submissionId: number) => {
    if (!selectedExamId) return;
    setSelectedSubmissionId(submissionId);
    setShowSubmissionText(false);
    setSubmissionText(null);
    await loadSubmissionDetail(selectedExamId, submissionId);
  };

  const handleGradeSubmission = async () => {
    if (!token || !selectedExamId || !selectedSubmissionId) return;
    setLoading({ grading: true });
    setError(null);
    try {
      await apiGradeSubmission(token, selectedExamId, selectedSubmissionId);
      await loadSubmissionDetail(selectedExamId, selectedSubmissionId);
      await loadSubmissions(selectedExamId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error calificando submission");
    } finally {
      setLoading({ grading: false });
    }
  };

  const handleToggleKeyText = async () => {
    if (!selectedExamId) return;
    if (!examKeyText) {
      await loadKeyText(selectedExamId);
    }
    setShowKeyText((prev) => !prev);
  };

  const handleToggleSubmissionText = async () => {
    if (!token || !selectedExamId || !selectedSubmissionId) return;
    if (!submissionText) {
      setLoading({ submissionDetail: true });
      try {
        const data = await apiGetExamSubmissionText(token, selectedExamId, selectedSubmissionId);
        setSubmissionText(data.raw_text);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error cargando texto");
      } finally {
        setLoading({ submissionDetail: false });
      }
    }
    setShowSubmissionText((prev) => !prev);
  };

  return (
    <div className="min-h-screen bg-[#f0f5ff] p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-[#1a2b4a]">Examenes</h1>
          <p className="text-sm text-gray-400 mt-1">
            Crea examenes, carga el examen base y califica con IA.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-100 text-red-600 text-xs rounded-xl px-4 py-2">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
          <div className="space-y-5">
            <ExamCreateCard
              title={title}
              description={description}
              loading={loading.exams}
              onTitleChange={setTitle}
              onDescriptionChange={setDescription}
              onCreate={handleCreateExam}
            />

            <ExamListCard
              exams={exams}
              selectedExamId={selectedExamId}
              loading={loading.exams}
              formatDate={formatDate}
              onSelect={setSelectedExamId}
            />
          </div>

          <div className="space-y-5">
            {!activeExam ? (
              <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm text-sm text-gray-400">
                Selecciona un examen para comenzar.
              </div>
            ) : (
              <>
                <ExamKeyCard
                  exam={activeExam}
                  examKeyText={examKeyText}
                  showKeyText={showKeyText}
                  keyFileName={keyFileName}
                  loadingKey={loading.key}
                  inputRef={keyInputRef}
                  formatDate={formatDate}
                  onToggleText={handleToggleKeyText}
                  onUpload={handleUploadKey}
                  onFileNameChange={setKeyFileName}
                />

                <ExamSubmissionsCard
                  studentName={studentName}
                  onStudentNameChange={setStudentName}
                  submissionFileName={submissionFileName}
                  onFileNameChange={setSubmissionFileName}
                  inputRef={submissionInputRef}
                  onUpload={handleUploadSubmission}
                  submissions={submissions}
                  selectedSubmissionId={selectedSubmissionId}
                  loading={loading.submissions}
                  formatDate={formatDate}
                  onSelect={handleSelectSubmission}
                />

                <ExamResultCard
                  activeSubmission={activeSubmission}
                  selectedSubmissionDetail={selectedSubmissionDetail}
                  submissionText={submissionText}
                  showSubmissionText={showSubmissionText}
                  loadingDetail={loading.submissionDetail}
                  loadingGrading={loading.grading}
                  onToggleText={handleToggleSubmissionText}
                  onGrade={handleGradeSubmission}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
