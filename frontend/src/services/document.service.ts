import { API_BASE_URL } from "../lib/api";

export interface DocumentResponse {
  id: number;
  user_id: number;
  filename: string;
  chunks_indexed: number;
  description: string | null;
  document_type: string;
  uploaded_at: string;
}

export interface UploadResponse {
  filename: string;
  chunks_indexed: number;
  message: string;
}

export interface GlobalDocument {
  id: string;
  filename: string;
  chunks_indexed: number;
  scope: "global";
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Error ${res.status}`);
  }
  return res.json();
}

export async function apiGetUserDocuments(token: string): Promise<DocumentResponse[]> {
  const res = await fetch(`${API_BASE_URL}/documents`, {
    headers: authHeaders(token),
  });
  return handleResponse<DocumentResponse[]>(res);
}

export async function apiUploadUserDocument(
  token: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return handleResponse<UploadResponse>(res);
}

export async function apiDeleteDocument(token: string, documentId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Error ${res.status}`);
  }
}

export async function apiGetGlobalDocuments(token: string): Promise<GlobalDocument[]> {
  const res = await fetch(`${API_BASE_URL}/documents/base`, {
    headers: authHeaders(token),
  });
  return handleResponse<GlobalDocument[]>(res);
}

export async function apiUploadGlobalDocument(
  token: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/upload/base`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
  return handleResponse<UploadResponse>(res);
}