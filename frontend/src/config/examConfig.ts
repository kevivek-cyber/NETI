/**
 * Legitimate Frontend UI Configuration
 * 
 * This file contains structure and display constants for the NEET exam.
 * It is purely frontend configuration and MUST NOT be confused with 
 * server-authoritative candidate or session data.
 */

export const examConfig = {
  examName: "National Eligibility cum Entrance Test (NEET)",
  totalQuestions: 180,
  totalMinutes: 180, // Default UI display fallback (not the authoritative timer)
  subjects: [
    { name: "Physics", count: 45 },
    { name: "Chemistry", count: 45 },
    { name: "Biology", count: 90 }
  ]
};
