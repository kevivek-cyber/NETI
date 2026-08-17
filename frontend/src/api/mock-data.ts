export interface CandidateInfo {
  name: string;
  rollNumber: string;
  photoUrl: string;
  examName: string;
  examCenter: string;
  seatNumber: string;
  examDate: string;
  examDuration: string;
  totalQuestions: number;
  subjects: { name: string; count: number }[];
}

export const mockData = {
  getCurrentCandidate: async (): Promise<CandidateInfo> => {
    // Simulate network delay
    await new Promise(r => setTimeout(r, 800));

    // Return the mock current candidate (would come from session/token)
    return {
      name: "Aarav Sharma",
      rollNumber: "NEET2026-000123",
      photoUrl: "", // Do not use random human photograph
      examName: "National Eligibility cum Entrance Test (NEET)",
      examCenter: "TCS iON Digital Zone,\nMumbai",
      seatNumber: "A-42",
      examDate: "12 August 2026 • 10:00 AM",
      examDuration: "3 Hours",
      totalQuestions: 180,
      subjects: [
        { name: "Physics", count: 45 },
        { name: "Chemistry", count: 45 },
        { name: "Biology", count: 90 }
      ]
    };
  }
};
