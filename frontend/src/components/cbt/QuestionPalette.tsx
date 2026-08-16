import { useEffect, useRef } from "react";
import { Question } from "../../api/api";
import clsx from "clsx";
import { ExamStats } from "../../utils/examStats";
import { Subject } from "./SubjectTabs";

interface QuestionPaletteProps {
  questions: Question[];
  currentQuestionIndex: number; // Global index
  answers: Record<string, number>;
  markedForReview: Record<string, boolean>;
  visited?: Record<string, boolean>;
  onQuestionSelect: (index: number) => void;
  activeSubject: Subject;
  onSubjectChange: (subject: Subject) => void;
  overallStats: ExamStats;
}

const css = `
  .palette-scroll::-webkit-scrollbar {
    width: 6px;
  }
  .palette-scroll::-webkit-scrollbar-track {
    background: #F5F8FC;
  }
  .palette-scroll::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 4px;
  }
  .palette-bubble {
    width: 38px;
    height: 38px;
    border-radius: 8px; /* Rounded square */
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    border: 1px solid transparent;
    cursor: pointer;
    position: relative;
    background: #FFFFFF;
    color: #475569;
    box-shadow: 0 1px 2px rgba(23,42,70,0.05);
    transition: all 0.15s;
    outline: none;
  }
  .palette-bubble:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(23,42,70,0.08);
  }
  .palette-bubble:focus-visible {
    box-shadow: 0 0 0 2px #2563EB;
  }
  
  .palette-bubble.not-visited {
    background: #F1F5F9;
    color: #475569;
    border-color: #CBD5E1;
    border-radius: 8px;
  }
  .palette-bubble.not-answered {
    background: #EE7A7A;
    color: #FFFFFF;
    border-color: #E26060;
    border-bottom-left-radius: 12px;
    border-top-right-radius: 12px;
    border-top-left-radius: 4px;
    border-bottom-right-radius: 4px;
  }
  .palette-bubble.answered {
    background: #10B981;
    color: #FFFFFF;
    border-color: #059669;
    border-top-left-radius: 12px;
    border-bottom-right-radius: 12px;
    border-top-right-radius: 4px;
    border-bottom-left-radius: 4px;
  }
  .palette-bubble.review {
    background: #8B5CF6;
    color: #FFFFFF;
    border-color: #7C3AED;
    border-radius: 50%;
  }
  .palette-bubble.answered-review {
    background: #8B5CF6;
    color: #FFFFFF;
    border-color: #7C3AED;
    border-radius: 50%;
  }
  .palette-bubble.answered-review::after {
    content: '';
    position: absolute;
    bottom: -2px;
    right: -2px;
    width: 12px;
    height: 12px;
    background: #10B981;
    border-radius: 50%;
    border: 2px solid #FFFFFF;
  }
  .palette-bubble.current {
    box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4px #3B82F6;
    z-index: 2;
  }

  .legend-dot {
    width: 14px;
    height: 14px;
    border-radius: 4px;
    flex-shrink: 0;
  }
`;

import { getDisplaySubject } from "./ExamClient";

export function QuestionPalette({
  questions,
  currentQuestionIndex,
  answers,
  markedForReview,
  visited = {},
  onQuestionSelect,
  activeSubject,
  onSubjectChange,
  overallStats,
}: QuestionPaletteProps) {
  
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
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
  
  return (
    <div style={{ 
      width: '300px', 
      flexShrink: 0, 
      display: 'flex', 
      flexDirection: 'column', 
      background: '#FFFFFF', 
      borderRight: '1px solid #D9E2EF',
      fontFamily: '"Inter", sans-serif',
      minHeight: 0
    }}>
      <style>{css}</style>
      
      {/* Legend Header */}
      <div style={{ padding: '24px 20px', borderBottom: '1px solid #D9E2EF', background: '#F5F8FC' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#172A46', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Question Palette</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '11px', color: '#475569', fontWeight: 600 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="legend-dot" style={{ background: '#F1F5F9', border: '1px solid #CBD5E1', borderRadius: '4px' }}></div> Not Visited
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="legend-dot" style={{ background: '#EE7A7A', borderBottomLeftRadius: '6px', borderTopRightRadius: '6px', borderTopLeftRadius: '2px', borderBottomRightRadius: '2px' }}></div> Not Answered
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="legend-dot" style={{ background: '#10B981', borderTopLeftRadius: '6px', borderBottomRightRadius: '6px', borderTopRightRadius: '2px', borderBottomLeftRadius: '2px' }}></div> Answered
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="legend-dot" style={{ background: '#8B5CF6', borderRadius: '50%' }}></div> Marked
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', gridColumn: 'span 2' }}>
            <div className="legend-dot" style={{ background: '#8B5CF6', borderRadius: '50%', position: 'relative' }}>
              <div style={{ position: 'absolute', bottom: '-2px', right: '-2px', width: '6px', height: '6px', background: '#10B981', borderRadius: '50%', border: '1px solid #FFFFFF' }}></div>
            </div> Answered & Marked
          </div>
        </div>
      </div>

      {/* Questions Scroll Area */}
      <div 
        className="palette-scroll"
        ref={scrollContainerRef}
        style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '12px 20px' }}
      >
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0 12px 0', borderBottom: '2px solid #2563EB', marginBottom: '16px' }}>
            <span style={{ fontSize: '14px', fontWeight: 700, color: '#2563EB' }}>
              {activeSubject} <span style={{ color: '#64748B', fontWeight: 600, fontSize: '12px', marginLeft: '4px' }}>({questions.filter(q => getDisplaySubject(q.subject) === activeSubject).length})</span>
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
            {questions.filter(q => getDisplaySubject(q.subject) === activeSubject).map((q) => {
              const globalIndex = q.number - 1; // Assuming sequential mapping from Checkin
              const isAnswered = answers[q.item_id] !== undefined;
              const isMarked = markedForReview[q.item_id];
              const isCurrent = globalIndex === currentQuestionIndex;
              const isVisited = visited[q.item_id] || isCurrent;

              let statusClass = "not-visited";
              if (isAnswered && isMarked) statusClass = "answered-review";
              else if (isAnswered) statusClass = "answered";
              else if (isMarked) statusClass = "review";
              else if (isVisited) statusClass = "not-answered";

              return (
                <button
                  key={q.item_id}
                  className={clsx("palette-bubble", statusClass, isCurrent && "current")}
                  onClick={() => onQuestionSelect(globalIndex)}
                  aria-current={isCurrent ? "true" : undefined}
                >
                  {q.number}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
