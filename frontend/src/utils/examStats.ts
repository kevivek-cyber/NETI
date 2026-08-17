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
 * - notVisited: question index is not in `visited` map.
 * - notAnswered: visited, but no answer and not marked.
 * - answered: has an answer, not marked.
 * - marked: marked for review, but no answer.
 * - answeredAndMarked: has an answer AND is marked for review.
 */
export function calculateExamStats(
  total: number,
  answers: Record<number, number>,
  markedForReview: Record<number, boolean>,
  visited: Record<number, boolean>
): ExamStats {
  let answered = 0;
  let notAnswered = 0;
  let marked = 0;
  let answeredAndMarked = 0;
  let notVisited = 0;

  for (let i = 0; i < total; i++) {
    const hasVisited = !!visited[i];
    const hasAnswer = answers[i] !== undefined;
    const isMarked = !!markedForReview[i];

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
    total,
    answered,
    notAnswered,
    marked,
    answeredAndMarked,
    notVisited,
    totalAnswered: answered + answeredAndMarked
  };
}
