import { api, type SessionInfo, type IssuedPaper } from './api';

export interface SessionInfoMock extends SessionInfo {
  duration_seconds: number;
}

export interface IssuedPaperMock extends IssuedPaper {
  started_at: number;
}

/**
 * apiMocks wraps the strict backend api.ts contract to provide 
 * frontend-only fields needed for CBT functionality until Role 3 implements them.
 * This preserves api.ts as a pure reflection of the backend contract.
 */
export const apiMocks = {
  ...api,

  openSession: async (blueprint = "DEMO"): Promise<SessionInfoMock> => {
    // Mocking to avoid backend 500 error during frontend development
    // const session = await api.openSession(blueprint);
    return {
      session_id: "mock-session-123",
      blueprint: blueprint,
      questions: 180,
      marks: 720,
      bank_version: "v1.0.0",
      blueprint_hash: "mock-blueprint-hash",
      duration_seconds: 10800, // Mock: 3 hours default duration
    };
  },

  issuePaper: async (candidateId: string): Promise<IssuedPaperMock> => {
    // Mocking to avoid backend 500 error during frontend development
    // const paper = await api.issuePaper(candidateId);
    return {
      pseudonym: candidateId,
      leaf_index: 42,
      paper_hash: "mock-paper-hash-abcdef1234567890",
      paper: {
        blueprint: "DEMO",
        bank_version: "v1.0.0",
        questions: Array.from({ length: 180 }).map((_, i) => {
          const number = i + 1;
          let subject = "Physics";
          if (number > 45 && number <= 90) subject = "Chemistry";
          if (number > 90) subject = "Biology";

          return {
            number,
            item_id: `q${number}`,
            subject,
            stem: `This is a mock ${subject} question (Overall Question No. ${number}). Choose the correct option below.`,
            options: [
              "Option A for this question",
              "Option B for this question",
              "Option C for this question",
              "Option D for this question"
            ]
          };
        })
      },
      started_at: Date.now(), // Mock: Exam started right now
    };
  },

  getServerTime: async () => {
    // Mock: Returns the current local time as a substitute for server time.
    // In a real implementation, this would hit GET /session/time.
    return { serverTime: Date.now() };
  },

  /**
   * TODO(Role 3): Implement the real synchronization endpoint.
   * This endpoint should accept the current candidate state (answers, current question)
   * and persist it on the backend to allow cross-device recovery.
   */
  syncSession: async (candidateId: string, payload: any): Promise<void> => {
    // Mock: Simulate network latency for syncing data
    return new Promise((resolve) => setTimeout(resolve, 500));
  }
};
