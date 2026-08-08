import { Question } from "../../api/api";
import { ExamStats } from "../../utils/examStats";

interface QuestionInfoProps {
  question: Question;
  subjectStats: ExamStats;
}

export function QuestionInfo({ question, subjectStats }: QuestionInfoProps) {
  return (
    <div className="cbt-question-info-sidebar">
      <div className="info-panel">
        <h3 className="panel-title">QUESTION INFO</h3>
        <ul className="info-list">
          <li>
            <span className="info-label">Subject</span>
            <span className="info-value">{question.subject.toUpperCase()}</span>
          </li>
          <li>
            <span className="info-label">Chapter</span>
            <span className="info-value">General Mock</span>
          </li>
          <li>
            <span className="info-label">Question Type</span>
            <span className="info-value">MCQ (Single Answer)</span>
          </li>
          <li>
            <span className="info-label">Marks</span>
            <span className="info-value text-success" style={{ fontWeight: 600 }}>+4</span>
          </li>
          <li>
            <span className="info-label">Negative Marks</span>
            <span className="info-value text-danger" style={{ fontWeight: 600 }}>-1</span>
          </li>
        </ul>
      </div>

      <div className="info-panel">
        <h3 className="panel-title">SECTION SUMMARY ({question.subject.toUpperCase()})</h3>
        <ul className="info-list summary-list">
          <li>
            <span className="info-label"><span className="palette-bubble answered" style={{ width: 20, height: 20, fontSize: 0 }} /> Answered</span>
            <span className="info-value">{subjectStats.answered}</span>
          </li>
          <li>
            <span className="info-label"><span className="palette-bubble not-answered" style={{ width: 20, height: 20, fontSize: 0 }} /> Not Answered</span>
            <span className="info-value">{subjectStats.notAnswered}</span>
          </li>
          <li>
            <span className="info-label"><span className="palette-bubble review" style={{ width: 20, height: 20, fontSize: 0 }} /> Marked for Review</span>
            <span className="info-value">{subjectStats.marked}</span>
          </li>
          <li>
            <span className="info-label"><span className="palette-bubble answered-review" style={{ width: 20, height: 20, fontSize: 0 }} /> Answered & Marked</span>
            <span className="info-value">{subjectStats.answeredAndMarked}</span>
          </li>
          <li className="summary-total">
            <span className="info-label">Total Questions</span>
            <span className="info-value">{subjectStats.total}</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
