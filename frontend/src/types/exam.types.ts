export interface ExamResponse {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  created_at: string;
}

export interface ExamCreatePayload {
  title: string;
  description?: string | null;
}

export interface ExamKeyResponse {
  id: number;
  exam_id: number;
  filename: string;
  questions_count: number;
  created_at: string;
}

export interface ExamKeyTextResponse {
  exam_id: number;
  raw_text: string;
}

export interface ExamSubmissionResponse {
  id: number;
  exam_id: number;
  student_name: string | null;
  filename: string;
  answers_count: number;
  created_at: string;
}

export interface ExamSubmissionTextResponse {
  submission_id: number;
  raw_text: string;
}

export interface ExamQuestionResultResponse {
  id: number;
  question_number: number;
  question_text: string | null;
  correct_answer: string;
  student_answer: string | null;
  score: number;
  max_score: number;
  verdict: string;
  confidence: number;
  reason: string;
}

export interface ExamGradeResponse {
  id: number;
  submission_id: number;
  total_score: number;
  max_score: number;
  percentage: number;
  confidence: number;
  needs_review: boolean;
  provisional: boolean;
  feedback: string;
  created_at: string;
  question_results: ExamQuestionResultResponse[];
}

export interface ExamSubmissionDetailResponse {
  id: number;
  exam_id: number;
  student_name: string | null;
  filename: string;
  answers_count: number;
  created_at: string;
  grade: ExamGradeResponse | null;
}
