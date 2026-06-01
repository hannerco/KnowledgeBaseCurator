import { API_BASE_URL } from "../lib/api";
import type {
  ExamCreatePayload,
  ExamGradeResponse,
  ExamKeyResponse,
  ExamKeyTextResponse,
  ExamResponse,
  ExamSubmissionDetailResponse,
  ExamSubmissionResponse,
  ExamSubmissionTextResponse,
} from "../types/exam.types";

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

function jsonHeaders(token: string) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Error ${res.status}`);
  }
  return res.json();
}

export async function apiGetExams(token: string): Promise<ExamResponse[]> {
  const res = await fetch(`${API_BASE_URL}/exams/`, {
    headers: authHeaders(token),
  });
  return handleResponse<ExamResponse[]>(res);
}

export async function apiCreateExam(
  token: string,
  payload: ExamCreatePayload
): Promise<ExamResponse> {
  const res = await fetch(`${API_BASE_URL}/exams/`, {
    method: "POST",
    headers: jsonHeaders(token),
    body: JSON.stringify(payload),
  });
  return handleResponse<ExamResponse>(res);
}

export async function apiGetExam(
  token: string,
  examId: number
): Promise<ExamResponse> {
  const res = await fetch(`${API_BASE_URL}/exams/${examId}`, {
    headers: authHeaders(token),
  });
  return handleResponse<ExamResponse>(res);
}

export async function apiUploadExamKey(
  token: string,
  examId: number,
  file: File
): Promise<ExamKeyResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/exams/${examId}/key`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return handleResponse<ExamKeyResponse>(res);
}

export async function apiGetExamKeyText(
  token: string,
  examId: number
): Promise<ExamKeyTextResponse> {
  const res = await fetch(`${API_BASE_URL}/exams/${examId}/key/text`, {
    headers: authHeaders(token),
  });
  return handleResponse<ExamKeyTextResponse>(res);
}

export async function apiUploadExamSubmission(
  token: string,
  examId: number,
  file: File,
  studentName?: string
): Promise<ExamSubmissionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (studentName) {
    formData.append("student_name", studentName);
  }

  const res = await fetch(`${API_BASE_URL}/exams/${examId}/submissions`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return handleResponse<ExamSubmissionResponse>(res);
}

export async function apiGetExamSubmissions(
  token: string,
  examId: number
): Promise<ExamSubmissionResponse[]> {
  const res = await fetch(`${API_BASE_URL}/exams/${examId}/submissions`, {
    headers: authHeaders(token),
  });
  return handleResponse<ExamSubmissionResponse[]>(res);
}

export async function apiGetExamSubmission(
  token: string,
  examId: number,
  submissionId: number
): Promise<ExamSubmissionDetailResponse> {
  const res = await fetch(
    `${API_BASE_URL}/exams/${examId}/submissions/${submissionId}`,
    { headers: authHeaders(token) }
  );
  return handleResponse<ExamSubmissionDetailResponse>(res);
}

export async function apiGetExamSubmissionText(
  token: string,
  examId: number,
  submissionId: number
): Promise<ExamSubmissionTextResponse> {
  const res = await fetch(
    `${API_BASE_URL}/exams/${examId}/submissions/${submissionId}/text`,
    { headers: authHeaders(token) }
  );
  return handleResponse<ExamSubmissionTextResponse>(res);
}

export async function apiGradeSubmission(
  token: string,
  examId: number,
  submissionId: number
): Promise<ExamGradeResponse> {
  const res = await fetch(
    `${API_BASE_URL}/exams/${examId}/submissions/${submissionId}/grade`,
    {
      method: "POST",
      headers: authHeaders(token),
    }
  );
  return handleResponse<ExamGradeResponse>(res);
}
