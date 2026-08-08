import { ExamStats } from "../../utils/examStats";

interface SubmitConfirmationProps {
  stats: ExamStats;
  onConfirm: () => void;
  onCancel: () => void;
}

export function SubmitConfirmation({
  stats,
  onConfirm,
  onCancel,
}: SubmitConfirmationProps) {
  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="submit-modal-title">
      <div className="modal-content warning" style={{ maxWidth: '500px', borderTopWidth: '4px', borderColor: 'var(--danger)' }}>
        <h2 id="submit-modal-title">Submit Examination?</h2>
        <p className="muted" style={{ fontSize: '1.05rem', marginBottom: '1.5rem' }}>
          Before submitting, please review your responses.
        </p>
        
        <ul className="summary-list" style={{ background: 'var(--bg)', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
          <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}><span>Total Questions</span> <strong>{stats.total}</strong></li>
          <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}><span>Answered</span> <strong style={{ color: 'var(--success)' }}>{stats.answered}</strong></li>
          <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}><span>Not Answered</span> <strong style={{ color: 'var(--muted)' }}>{stats.notAnswered}</strong></li>
          <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}><span>Marked for Review</span> <strong style={{ color: 'var(--warning)' }}>{stats.marked}</strong></li>
          <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}><span>Answered & Marked</span> <strong style={{ color: 'var(--purple)' }}>{stats.answeredAndMarked}</strong></li>
          <li style={{ display: 'flex', justifyContent: 'space-between' }}><span>Not Visited</span> <strong>{stats.notVisited}</strong></li>
        </ul>

        <div style={{ background: 'var(--danger-soft)', color: 'var(--danger)', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--danger)', marginTop: '1.5rem', textAlign: 'center', fontWeight: 600 }}>
          Once submitted, you cannot modify your answers.
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <button className="secondary" onClick={onCancel} style={{ width: '150px' }}>
            Cancel
          </button>
          <button className="danger" onClick={onConfirm} style={{ width: '200px' }}>
            Submit Examination
          </button>
        </div>
      </div>
    </div>
  );
}
