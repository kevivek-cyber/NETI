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

export interface CheckInRequest {
  candidate_id: string;
  session_id: string;
}

export interface CheckInResponse {
  status: string;
  candidate_id: string;
  session_state: string;
}

export interface IssuePaperRequest {
  candidate_id: string;
  session_id: string;
}

export interface IssuePaperResponse {
  candidate_id: string;
  paper_hash: string;
  session_state: string;
  paper: SealedPaper;
}

export interface ResponseEvent {
  question_id: string;
  selected_option_index: number;
  timestamp_iso: string;
}

export interface SubmitRequest {
  candidate_id: string;
  session_id: string;
  events: ResponseEvent[];
  expected_response_chain: string;
}

export interface MerklePathStep {
  side: "L" | "R";
  hash: string;
}

export interface InclusionProof {
  index: number;
  leaf: string;
  path: MerklePathStep[];
}

export interface ReceiptPayload {
  candidate_pseudonym: string;
  session_id: string;
  paper_hash: string;
  response_chain_digest: string;
  merkle_root: string;
  inclusion_proof: InclusionProof;
}

export interface SubmitResponse {
  status: string;
  candidate_id: string;
  session_state: string;
  receipt: ReceiptPayload;
  receipt_hash: string;
}

export interface ShareInput {
  index: number;
  share_hex: string;
}

export interface UnlockRequest {
  session_id: string;
  shares: ShareInput[];
}

export interface UnlockResponse {
  status: string;
  session_id: string;
  message: string;
}

// Dev: Vite proxies /api to localhost:8000.
// Prod: VITE_API_BASE points at the deployed API (set in render.yaml).
const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (err: any) {
    if (err.message === "Failed to fetch" || err.message.includes("NetworkError")) {
      throw new Error("Unable to connect to the server. Please check your network connection or contact an invigilator.");
    }
    throw err;
  }

  if (!response.ok) {
    let detail = "An unexpected error occurred.";
    try {
      const errorText = await response.text();
      detail = errorText;
      const parsed = JSON.parse(errorText);
      if (parsed.detail) {
        if (Array.isArray(parsed.detail)) {
          detail = parsed.detail.map((e: any) => e.msg).join(", ");
        } else {
          detail = parsed.detail;
        }
      }
    } catch (e) {
      // Not JSON, fallback to status codes
      if (response.status >= 500) {
        detail = "The server encountered an unexpected problem. Please contact an invigilator.";
      }
    }

    // Override generic server errors
    if (detail === "Internal Server Error" || response.status >= 500) {
      detail = "The server encountered an unexpected problem. Please contact an invigilator.";
    }

    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  ceremonyUnlock: (req: UnlockRequest) =>
    call<UnlockResponse>("/ceremony/unlock", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  checkIn: (req: CheckInRequest) =>
    call<CheckInResponse>("/exam/check-in", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  issuePaper: (req: IssuePaperRequest) =>
    call<IssuePaperResponse>("/exam/issue-paper", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  submitExam: (req: SubmitRequest) =>
    call<SubmitResponse>("/exam/submit", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  getServerTime: async () => {
    // Mock: Returns the current local time as a substitute for server time.
    // In a real implementation, this would hit GET /session/time.
    return { serverTime: Date.now() };
  },
};
