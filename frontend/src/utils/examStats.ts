import { Question } from "../api/api";

export interface ExamStats {
  total: number;
  answered: number;
  notAnswered: number;
  marked: number;
  answeredAndMarked: number;
  notVisited: number;
  // Convenience aggregated totals (not for the mutually exclusive breakdown)
  totalAnswered: number; 
}

/**
 * Calculates mutually exclusive examination statistics.
 * 
 * Rules:
 * - total = N
 * - answered + notAnswered + marked + answeredAndMarked + notVisited = total
 * 
 * Definitions:
 * - notVisited: item_id is not in `visited` map.
 * - notAnswered: visited, but no answer and not marked.
 * - answered: has an answer, not marked.
 * - marked: marked for review, but no answer.
 * - answeredAndMarked: has an answer AND is marked for review.
 */
export function calculateExamStats(
  questions: Question[],
  answers: Record<string, number>,
  markedForReview: Record<string, boolean>,
  visited: Record<string, boolean>
): ExamStats {
  let answered = 0;
  let notAnswered = 0;
  let marked = 0;
  let answeredAndMarked = 0;
  let notVisited = 0;

  for (const q of questions) {
    const id = q.item_id;
    const hasVisited = !!visited[id];
    const hasAnswer = answers[id] !== undefined;
    const isMarked = !!markedForReview[id];

    if (!hasVisited) {
      notVisited++;
    } else {
      if (hasAnswer && isMarked) {
        answeredAndMarked++;
      } else if (hasAnswer && !isMarked) {
        answered++;
      } else if (!hasAnswer && isMarked) {
        marked++;
      } else {
        notAnswered++;
      }
    }
  }

  return {
    total: questions.length,
    answered,
    notAnswered,
    marked,
    answeredAndMarked,
    notVisited,
    totalAnswered: answered + answeredAndMarked
  };
}
