/**
 * Backend contract. This file IS the interface between role 3 and role 4 —
 * if the API changes, change it here first and the compiler finds the rest.
 *
 * Kept as a literal mirror of backend/app/api/{exam_router,ceremony_router}.py
 * — every path, request body, and response shape below is taken directly
 * from those routers' Pydantic models, not from an earlier plan for them.
 * If this drifts from the routers again, every call in this file breaks
 * against a live backend even though `npm run build` stays green, because
 * nothing here is checked against the actual FastAPI schema at build time.
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

// Response of POST /exam/issue-paper. Note what the backend does NOT
// return: no pseudonym, no leaf_index. The candidate is identified to the
// backend by candidate_id on every call (it re-derives the pseudonym
// itself); leaf_index is assigned server-side and only surfaces later,
// inside the inclusion proof on the /exam/submit receipt.
export interface IssuedPaper {
  candidate_id: string;
  paper_hash: string;
  session_state: string;
  paper: SealedPaper;
  // TODO(role 3): expose exam start time / duration. Neither issue-paper
  // nor any other endpoint currently returns them; the CBT timer has
  // nothing real to read yet. See useExamTimer.
}

export interface ResponseEvent {
  question_id: string;
  selected_option_index: number;
  timestamp_iso: string;
}

export interface InclusionProof {
  index: number;
  leaf: string;
  path: { side: "L" | "R"; hash: string }[];
}

export interface Receipt {
  candidate_pseudonym: string;
  session_id: string;
  paper_hash: string;
  response_chain_digest: string;
  merkle_root: string;
  inclusion_proof: InclusionProof;
}

export interface SubmitResult {
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
    call<{ status: string; candidate_id: string; session_state: string }>(
      "/exam/check-in",
      { method: "POST", body: JSON.stringify({ candidate_id: candidateId, session_id: sessionId }) },
    ),

  issuePaper: (candidateId: string, sessionId: string) =>
    call<IssuedPaper>("/exam/issue-paper", {
      method: "POST",
      body: JSON.stringify({ candidate_id: candidateId, session_id: sessionId }),
    }),

  submitExam: (
    candidateId: string,
    sessionId: string,
    events: ResponseEvent[],
    expectedResponseChain: string,
  ) =>
    call<SubmitResult>("/exam/submit", {
      method: "POST",
      body: JSON.stringify({
        candidate_id: candidateId,
        session_id: sessionId,
        events,
        expected_response_chain: expectedResponseChain,
      }),
    }),

  // MOCK: no backend endpoint exposes server time or an exam-configuration
  // lookup yet (there is no /session route at all — the earlier
  // `openSession` here pointed at one that was never built). Left as a
  // local-time stand-in until role 3 adds one; do not remove this comment
  // when that lands or the next person re-adds a call to a route that
  // still doesn't exist.
  getServerTime: async () => {
    return { serverTime: Date.now() };
  },
};

// TODO(role 4): `submitExam` needs `events` — the ordered, timestamped log
// of every answer change during the exam — and `expectedResponseChain`,
// the final SHA-256 hash of replaying that log per INTEGRITY.md §8. Neither
// exists on the client today: ExamClient/useAutosave only ever keep the
// current answers snapshot, not a per-change event history, and there is
// no client-side implementation of the domain-separated hashing in
// backend/app/ledger/canonical.py + hashing.py to fold that log into a
// digest. Building that hashing needs to reproduce canonical_bytes()
// (sorted-key, no-whitespace JSON, UTF-8) and the 0x03 domain tag exactly,
// since backend/app/ledger/hashing.py documents this as "a permanent
// public contract" that a standalone verifier depends on byte-for-byte —
// get it wrong here and every receipt this client produces is invalid.
// CUSTODY.md §6.3 anticipates this exact browser-side hashing (WebCrypto,
// no server) for the receipt verifier; the same routine can build the
// submission digest here. Do not invent a simplified hash in the
// meantime — a client that "submits" with a wrong digest fails
// ResponseChain.verify_chain server-side and the candidate's exam is
// rejected, which is worse than the button being visibly unfinished.
