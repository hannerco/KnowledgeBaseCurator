import { create } from "zustand";
import type {
  ExamResponse,
  ExamSubmissionDetailResponse,
  ExamSubmissionResponse,
} from "../types/exam.types";

interface LoadingState {
  exams: boolean;
  key: boolean;
  submissions: boolean;
  submissionDetail: boolean;
  grading: boolean;
}

interface ExamStore {
  exams: ExamResponse[];
  selectedExamId: number | null;
  submissions: ExamSubmissionResponse[];
  selectedSubmissionId: number | null;
  selectedSubmissionDetail: ExamSubmissionDetailResponse | null;
  examKeyText: string | null;
  loading: LoadingState;
  error: string | null;

  setExams: (exams: ExamResponse[]) => void;
  setSelectedExamId: (examId: number | null) => void;
  setSubmissions: (submissions: ExamSubmissionResponse[]) => void;
  setSelectedSubmissionId: (submissionId: number | null) => void;
  setSelectedSubmissionDetail: (detail: ExamSubmissionDetailResponse | null) => void;
  setExamKeyText: (text: string | null) => void;
  setLoading: (partial: Partial<LoadingState>) => void;
  setError: (error: string | null) => void;
  resetSelection: () => void;
}

export const useExamStore = create<ExamStore>((set) => ({
  exams: [],
  selectedExamId: null,
  submissions: [],
  selectedSubmissionId: null,
  selectedSubmissionDetail: null,
  examKeyText: null,
  loading: {
    exams: false,
    key: false,
    submissions: false,
    submissionDetail: false,
    grading: false,
  },
  error: null,

  setExams: (exams) => set({ exams }),
  setSelectedExamId: (examId) => set({ selectedExamId: examId }),
  setSubmissions: (submissions) => set({ submissions }),
  setSelectedSubmissionId: (submissionId) => set({ selectedSubmissionId: submissionId }),
  setSelectedSubmissionDetail: (detail) => set({ selectedSubmissionDetail: detail }),
  setExamKeyText: (text) => set({ examKeyText: text }),
  setLoading: (partial) =>
    set((state) => ({
      loading: { ...state.loading, ...partial },
    })),
  setError: (error) => set({ error }),
  resetSelection: () =>
    set({
      selectedExamId: null,
      submissions: [],
      selectedSubmissionId: null,
      selectedSubmissionDetail: null,
      examKeyText: null,
      error: null,
      loading: {
        exams: false,
        key: false,
        submissions: false,
        submissionDetail: false,
        grading: false,
      },
    }),
}));
