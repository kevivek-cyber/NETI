import { Question } from "../../api/api";
import { ExamStats } from "../../utils/examStats";

interface QuestionInfoProps {
  question: Question;
  subjectStats: ExamStats;
}

const css = `
  .info-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #F1F5F9;
    font-size: 13px;
  }
  .info-stat-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
  .info-stat-label {
    color: #64748B;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .info-stat-val {
    color: #172A46;
    font-weight: 700;
  }
`;

export function QuestionInfo({ question, subjectStats }: QuestionInfoProps) {
  const answeredCount = subjectStats.answered + subjectStats.answeredAndMarked;
  const progressPercent = subjectStats.total > 0 ? Math.round((answeredCount / subjectStats.total) * 100) : 0;

  return (
    <div style={{ 
      width: '320px', 
      flexShrink: 0, 
      background: '#F5F8FC', 
      borderLeft: '1px solid #D9E2EF',
      padding: '24px',
      overflowY: 'auto',
      fontFamily: '"Inter", sans-serif'
    }}>
      <style>{css}</style>

      {/* Card 1: QUESTION INFO */}
      <div style={{ background: '#FFFFFF', border: '1px solid #D9E2EF', borderRadius: '12px', padding: '20px', marginBottom: '24px', boxShadow: '0 2px 4px rgba(23,42,70,0.02)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '12px', color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Question Info</h3>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="info-stat-row">
            <span className="info-stat-label">Subject</span>
            <span className="info-stat-val" style={{ color: '#2563EB' }}>{question.subject.toUpperCase()}</span>
          </div>
          <div className="info-stat-row">
            <span className="info-stat-label">Chapter</span>
            <span className="info-stat-val">General Mock</span>
          </div>
          <div className="info-stat-row">
            <span className="info-stat-label">Question Type</span>
            <span className="info-stat-val">MCQ (Single)</span>
          </div>
          <div className="info-stat-row">
            <span className="info-stat-label">Marks</span>
            <span className="info-stat-val" style={{ color: '#16A34A' }}>+4</span>
          </div>
          <div className="info-stat-row">
            <span className="info-stat-label">Negative Marks</span>
            <span className="info-stat-val" style={{ color: '#EF4444' }}>-1</span>
          </div>
        </div>
      </div>

      {/* Card 2: SECTION PROGRESS */}
      <div style={{ background: '#FFFFFF', border: '1px solid #D9E2EF', borderRadius: '12px', padding: '20px', boxShadow: '0 2px 4px rgba(23,42,70,0.02)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '12px', color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Section Progress</h3>
        
        {/* Progress Bar */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '12px', fontWeight: 600 }}>
            <span style={{ color: '#172A46' }}>Completion</span>
            <span style={{ color: '#2563EB' }}>{progressPercent}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: '#E2E8F0', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${progressPercent}%`, height: '100%', background: '#2563EB', borderRadius: '4px' }}></div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="info-stat-row">
            <span className="info-stat-label">
              <div style={{ width: 12, height: 12, borderRadius: 3, background: '#F0FDF4', border: '1px solid #86EFAC' }}></div> Answered
            </span>
            <span className="info-stat-val">{subjectStats.answered}</span>
          </div>
          <div className="info-stat-row">
            <span className="info-stat-label">
              <div style={{ width: 12, height: 12, borderRadius: 3, background: '#FEF2F2', border: '1px solid #FCA5A5' }}></div> Not Answered
            </span>
            <span className="info-stat-val">{subjectStats.notAnswered}</span>
          </div>
          <div className="info-stat-row">
            <span className="info-stat-label">
              <div style={{ width: 12, height: 12, borderRadius: 3, background: '#F5F3FF', border: '1px solid #C4B5FD' }}></div> Marked for Review
            </span>
            <span className="info-stat-val">{subjectStats.marked}</span>
          </div>
          <div className="info-stat-row">
            <span className="info-stat-label">
              <div style={{ width: 12, height: 12, borderRadius: 3, background: '#16A34A', position: 'relative' }}>
                 <div style={{ position: 'absolute', bottom: -2, right: -2, width: 6, height: 6, borderRadius: '50%', background: '#8B5CF6', border: '1px solid #FFF' }}></div>
              </div> Ans & Marked
            </span>
            <span className="info-stat-val">{subjectStats.answeredAndMarked}</span>
          </div>
          <div className="info-stat-row" style={{ marginTop: '8px', paddingTop: '16px', borderTop: '1px dashed #E2E8F0' }}>
            <span className="info-stat-label" style={{ color: '#172A46', fontWeight: 700 }}>Total Questions</span>
            <span className="info-stat-val" style={{ fontSize: '16px' }}>{subjectStats.total}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
