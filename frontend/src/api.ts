/**
 * Backend contract. This file IS the interface between role 3 and role 4 —
 * if the API changes, change it here first and the compiler finds the rest.
 */

export interface Question {
  number: number;
  item_id: string;
  subject: string;
  stem: string;
  options: string[];
  // answer_index is deliberately absent: the served paper is sealed.
}

export interface SealedPaper {
  blueprint: string;
  bank_version: string;
  questions: Question[];
}

export interface IssuedPaper {
  candidate_id: string;
  paper_hash: string;
  session_state: string;
  paper: SealedPaper;
}

export interface SessionInfo {
  session_id: string;
  blueprint: string;
  questions: number;
  marks: number;
  bank_version: string;
  blueprint_hash: string;
}

export interface Receipt {
  candidate_pseudonym: string;
  session_id: string;
  paper_hash: string;
  response_chain_digest: string;
  merkle_root: string;
  inclusion_proof: {
    index: number;
    leaf: string;
    path: { side: "L" | "R"; hash: string }[];
  };
}

export interface CheckInResponse {
  status: string;
  candidate_id: string;
  session_state: string;
}

export interface ResponseEvent {
  question_id: string;
  selected_option_index: number;
  timestamp_iso: string;
}

export interface SubmitResponse {
  status: string;
  candidate_id: string;
  session_state: string;
  receipt: Receipt;
  receipt_hash: string;
}

// Dev: Vite proxies /api to localhost:8000.
// Prod: VITE_API_BASE points at the deployed API (set in render.yaml).
const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  checkIn: (candidateId: string, sessionId: string) =>
    call<CheckInResponse>("/exam/check-in", {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId, session_id: sessionId }),
    }),

  issuePaper: (candidateId: string, sessionId: string) =>
    call<IssuedPaper>("/exam/issue-paper", {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId, session_id: sessionId }),
    }),

  submitExam: (candidateId: string, sessionId: string, events: ResponseEvent[], expectedResponseChain: string) =>
    call<SubmitResponse>("/exam/submit", {
      method: "POST",
      body: JSON.stringify({
        candidate_id: candidateId,
        session_id: sessionId,
        events,
        expected_response_chain: expectedResponseChain,
      }),
    }),

  unlock: (sessionId: string, shares: { index: number; share_hex: string }[]) =>
    call<{ status: string; session_id: string; message: string }>("/ceremony/unlock", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, shares }),
    }),

  revealAnswers: (sessionId: string, shares: { index: number; share_hex: string }[]) =>
    call<{ status: string; session_id: string; message: string }>("/ceremony/reveal-answers", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, shares }),
    }),
};
