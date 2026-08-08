import { Question } from "../../api/api";
import clsx from "clsx";
import { Bookmark, Info } from "lucide-react";

interface QuestionCardProps {
  question: Question;
  subjectQuestionsCount: number;
  subjectQuestionIndex: number;
  selectedAnswer?: number;
  onAnswerSelect: (index: number) => void;
  onMarkReview: () => void;
}

export function QuestionCard({
  question,
  subjectQuestionsCount,
  subjectQuestionIndex,
  selectedAnswer,
  onAnswerSelect,
  onMarkReview
}: QuestionCardProps) {
  return (
    <div className="cbt-question-card">
      <div className="question-meta">
        <div className="question-title-group">
          <h2 className="question-title">
            Question {subjectQuestionIndex + 1} of {subjectQuestionsCount}
          </h2>
          <div className="question-subject-label" style={{ fontSize: '13px', color: '#475569', marginTop: '4px', fontWeight: 600 }}>
            SUBJECT:<br/>
            <span style={{ color: '#0F172A', fontSize: '14px' }}>{question.subject.toUpperCase()}</span>
          </div>
        </div>
        <button className="btn-icon muted" onClick={onMarkReview} style={{ fontSize: '0.9rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.25rem', border: 'none', background: 'transparent', cursor: 'pointer' }}>
          <Bookmark size={18} />
          Mark for Review
        </button>
      </div>

      <div className="overall-question-info">
        <Info size={16} className="text-primary" />
        <span>Overall Question No. {question.number}</span>
      </div>

      <p className="stem" id="question-stem">{question.stem}</p>

      <ul className="options" role="radiogroup" aria-labelledby="question-stem">
        {question.options.map((option: string, index: number) => {
          const isSelected = selectedAnswer === index;
          return (
            <li key={index}>
              <label className={clsx("option-label", isSelected && "selected")}>
                <input
                  type="radio"
                  name={`q-${question.number}`}
                  checked={isSelected}
                  onChange={() => onAnswerSelect(index)}
                  className="sr-only-radio"
                  aria-checked={isSelected}
                />
                <span className="option-indicator" aria-hidden="true">
                  <span className={clsx("option-indicator-inner", isSelected && "selected")} />
                </span>
                <span className="letter" aria-hidden="true">{"ABCD"[index]}</span>
                <span className="option-text">{option}</span>
              </label>
            </li>
          );
        })}
      </ul>

      <div className="question-footer-info">
        <Info size={16} className="muted" />
        <span>Choose the correct option and click on Save & Next to continue.</span>
      </div>
    </div>
  );
}
