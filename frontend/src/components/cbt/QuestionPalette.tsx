import { useEffect, useRef } from "react";
import { Question } from "../../api/api";
import clsx from "clsx";
import { ExamStats } from "../../utils/examStats";
import { Subject } from "./SubjectTabs";
import { ChevronDown, ChevronUp } from "lucide-react";

interface QuestionPaletteProps {
  questions: Question[];
  currentQuestionIndex: number; // Global index
  answers: Record<number, number>;
  markedForReview: Record<number, boolean>;
  visited?: Record<number, boolean>;
  onQuestionSelect: (index: number) => void;
  activeSubject: Subject;
  overallStats: ExamStats;
}

export function QuestionPalette({
  questions,
  currentQuestionIndex,
  answers,
  markedForReview,
  visited = {},
  onQuestionSelect,
  activeSubject,
  overallStats,
}: QuestionPaletteProps) {
  
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Automatically scroll to the current question bubble if it's out of view
    if (scrollContainerRef.current) {
      const currentBubble = scrollContainerRef.current.querySelector('.palette-bubble.current');
      if (currentBubble) {
        currentBubble.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest'
        });
      }
    }
  }, [currentQuestionIndex, activeSubject]);
  
  const subjects: { name: Subject; count: number }[] = [
    { name: "PHYSICS", count: 45 },
    { name: "CHEMISTRY", count: 45 },
    { name: "BIOLOGY", count: 90 },
  ];

  return (
    <div className="cbt-palette-section">
      <div className="palette-section-block" style={{ flexShrink: 0, padding: '16px' }}>
        <h3 className="section-header-title">QUESTIONS</h3>
        <div className="palette-legend" aria-hidden="true" style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px', fontSize: '11px', color: '#475569', fontWeight: 600 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="palette-bubble not-visited" style={{ width: 24, height: 24, fontSize: '0' }}></span> Not Visited
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="palette-bubble not-answered" style={{ width: 24, height: 24, fontSize: '0' }}></span> Not Answered
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="palette-bubble answered" style={{ width: 24, height: 24, fontSize: '0' }}></span> Answered
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="palette-bubble review" style={{ width: 24, height: 24, fontSize: '0' }}></span> Marked for Review
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="palette-bubble answered-review" style={{ width: 24, height: 24, fontSize: '0' }}></span> Answered & Marked
          </div>
        </div>
      </div>

      <div 
        className="subject-accordions" 
        ref={scrollContainerRef}
        style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '0 16px' }}
      >
        {subjects.map((subj) => {
          const isActive = activeSubject === subj.name;
          const subjectQuestions = questions.filter(q => q.subject.toUpperCase() === subj.name);
          
          return (
            <div key={subj.name} className="accordion-item">
              <button 
                className={clsx("accordion-header", isActive && "active")}
                onClick={() => {}}
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center', 
                  width: '100%', 
                  padding: '12px 0', 
                  background: 'transparent', 
                  border: 'none', 
                  borderBottom: '1px solid #bfdbfe',
                  cursor: 'default' 
                }}
              >
                <span className="accordion-title" style={{ fontSize: '13px', fontWeight: 600, color: isActive ? '#1d4ed8' : '#475569' }}>
                  {subj.name} ({subj.count})
                </span>
                {isActive ? <ChevronUp size={16} color="#1d4ed8" /> : <ChevronDown size={16} color="#64748b" />}
              </button>
              
              {isActive && (
                <div className="accordion-content" style={{ paddingTop: '8px', paddingBottom: '16px' }}>
                  <div className="palette-grid">
                    {subjectQuestions.map((q, index) => {
                      const globalIndex = q.number - 1;
                      const subjectQuestionNumber = index + 1;
                      const isAnswered = answers[q.number] !== undefined;
                      const isMarked = markedForReview[q.number];
                      const isCurrent = globalIndex === currentQuestionIndex;
                      const isVisited = visited[globalIndex] || isCurrent;

                      let statusClass = "not-visited";
                      
                      if (isAnswered && isMarked) statusClass = "answered-review";
                      else if (isAnswered) statusClass = "answered";
                      else if (isMarked) statusClass = "review";
                      else if (isVisited) statusClass = "not-answered";

                      return (
                        <button
                          key={q.number}
                          className={clsx("palette-bubble", statusClass, isCurrent && "current")}
                          onClick={() => onQuestionSelect(globalIndex)}
                          aria-current={isCurrent ? "true" : undefined}
                        >
                          {String(subjectQuestionNumber).padStart(2, '0')}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="palette-section-block overall-summary-block" style={{ flexShrink: 0, padding: '16px', background: '#dbeafe', borderTop: '1px solid #bfdbfe' }}>
        <h3 className="section-header-title" style={{ fontSize: '13px', fontWeight: 700, color: '#1e3a8a', margin: '0 0 12px 0' }}>OVERALL SUMMARY (180)</h3>
        <div className="overall-summary-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div className="summary-box success">
            <span className="summary-value">{overallStats.answered}</span>
            <span className="summary-label">Answered</span>
          </div>
          <div className="summary-box muted">
            <span className="summary-value">{overallStats.notAnswered}</span>
            <span className="summary-label">Not Answered</span>
          </div>
          <div className="summary-box warning">
            <span className="summary-value">{overallStats.marked}</span>
            <span className="summary-label">Marked</span>
          </div>
          <div className="summary-box purple">
            <span className="summary-value">{overallStats.answeredAndMarked}</span>
            <span className="summary-label">Answered &<br/>Marked</span>
          </div>
        </div>
      </div>
    </div>
  );
}
