import { useState } from "react";
import type { SealedPaper } from "../api";

interface Props {
  paper: SealedPaper;
  answers: Record<number, number>;
  onAnswer: (question: number, option: number) => void;
  onSubmit: () => void;
}

/**
 * The candidate's view of a paper.
 *
 * TODO(role 4): kiosk mode, countdown timer with server-signed drift
 * correction, autosave, offline tolerance via service worker.
 */
export function ExamClient({ paper, answers, onAnswer, onSubmit }: Props) {
  const [current, setCurrent] = useState(0);
  const question = paper.questions[current];
  const answered = Object.keys(answers).length;

  return (
    <div className="exam">
      <nav className="palette" aria-label="Question navigator">
        {paper.questions.map((q, i) => (
          <button
            key={q.number}
            className={[
              "chip",
              i === current ? "chip-current" : "",
              answers[q.number] !== undefined ? "chip-answered" : "",
            ].join(" ")}
            onClick={() => setCurrent(i)}
            aria-current={i === current}
          >
            {q.number}
          </button>
        ))}
      </nav>

      <section className="question">
        <div className="question-meta">
          <span className="tag">{question.subject}</span>
          <span className="muted">
            Question {question.number} of {paper.questions.length}
          </span>
        </div>

        <p className="stem">{question.stem}</p>

        <ul className="options">
          {question.options.map((option, index) => (
            <li key={index}>
              <label className={answers[question.number] === index ? "selected" : ""}>
                <input
                  type="radio"
                  name={`q-${question.number}`}
                  checked={answers[question.number] === index}
                  onChange={() => onAnswer(question.number, index)}
                />
                <span className="letter">{"ABCD"[index]}</span>
                <span>{option}</span>
              </label>
            </li>
          ))}
        </ul>

        <div className="controls">
          <button onClick={() => setCurrent((c) => Math.max(0, c - 1))} disabled={current === 0}>
            Previous
          </button>
          <button
            onClick={() => setCurrent((c) => Math.min(paper.questions.length - 1, c + 1))}
            disabled={current === paper.questions.length - 1}
          >
            Next
          </button>
          <span className="muted">
            {answered}/{paper.questions.length} answered
          </span>
          <button className="primary" onClick={onSubmit}>
            Submit
          </button>
        </div>
      </section>
    </div>
  );
}
