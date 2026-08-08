import { ExamStats } from "../../utils/examStats";

interface ExamProgressProps {
  stats: ExamStats;
}

export function ExamProgress({ stats }: ExamProgressProps) {
  return (
    <div className="cbt-progress" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem' }}>
      <span className="progress-stat">Answered: <strong className="text-success">{stats.answered}</strong></span>
      <span className="progress-stat">Not Answered: <strong className="muted">{stats.notAnswered}</strong></span>
      <span className="progress-stat">Marked: <strong className="text-warning">{stats.marked}</strong></span>
      <span className="progress-stat">Ans & Marked: <strong style={{ color: 'var(--purple)' }}>{stats.answeredAndMarked}</strong></span>
      <span className="progress-stat">Not Visited: <strong>{stats.notVisited}</strong></span>
      <span className="progress-stat">Total: <strong>{stats.total}</strong></span>
    </div>
  );
}
