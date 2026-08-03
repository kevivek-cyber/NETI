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
  pseudonym: string;
  leaf_index: number;
  paper_hash: string;
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
  leaf_index: number;
  leaf: string;
  root: string;
  path: { side: "L" | "R"; hash: string }[];
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  openSession: (blueprint = "DEMO") =>
    call<SessionInfo>(`/session/open?blueprint=${blueprint}`, { method: "POST" }),

  issuePaper: (candidateId: string) =>
    call<IssuedPaper>("/exam/paper", {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId }),
    }),

  receipt: (index: number) => call<Receipt>(`/ledger/receipt/${index}`),

  root: () => call<{ root: string; leaf_count: number }>("/ledger/root"),
};

// TODO(role 4): submit answers once role 3 exposes POST /exam/submit.
// The response chain (INTEGRITY.md section 8) is hashed server-side.
