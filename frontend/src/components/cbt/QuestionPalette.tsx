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
    background: #FFFFFF;
    color: #475569;
    border-color: #D9E2EF;
  }
  .palette-bubble.not-answered {
    background: #FEF2F2;
    color: #EF4444;
    border-color: #FCA5A5;
  }
  .palette-bubble.answered {
    background: #F0FDF4;
    color: #16A34A;
    border-color: #86EFAC;
  }
  .palette-bubble.review {
    background: #F5F3FF;
    color: #8B5CF6;
    border-color: #C4B5FD;
  }
  .palette-bubble.answered-review {
    background: #F0FDF4;
    color: #16A34A;
    border-color: #86EFAC;
  }
  .palette-bubble.answered-review::after {
    content: '';
    position: absolute;
    bottom: -4px;
    right: -4px;
    width: 12px;
    height: 12px;
    background: #8B5CF6;
    border-radius: 4px;
    border: 2px solid #FFFFFF;
  }
  .palette-bubble.current {
    box-shadow: 0 0 0 2px #FFFFFF, 0 0 0 4px #2563EB;
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
  
  const subjects: { name: Subject; count: number }[] = [
    { name: "PHYSICS", count: questions.filter(q => getDisplaySubject(q.subject) === "PHYSICS").length },
    { name: "CHEMISTRY", count: questions.filter(q => getDisplaySubject(q.subject) === "CHEMISTRY").length },
    { name: "BIOLOGY", count: questions.filter(q => getDisplaySubject(q.subject) === "BIOLOGY").length },
  ];

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
            <div className="legend-dot" style={{ background: '#FFFFFF', border: '1px solid #D9E2EF' }}></div> Not Visited
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="legend-dot" style={{ background: '#EF4444' }}></div> Not Answered
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="legend-dot" style={{ background: '#16A34A' }}></div> Answered
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="legend-dot" style={{ background: '#8B5CF6' }}></div> Marked
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', gridColumn: 'span 2' }}>
            <div className="legend-dot" style={{ background: '#16A34A', position: 'relative' }}>
              <div style={{ position: 'absolute', bottom: '-2px', right: '-2px', width: '6px', height: '6px', background: '#8B5CF6', borderRadius: '2px', border: '1px solid #FFFFFF' }}></div>
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
        {subjects.map((subj) => {
          const isActive = activeSubject === subj.name;
          const subjectQuestions = questions.filter(q => getDisplaySubject(q.subject) === subj.name);
          
          return (
            <div key={subj.name} style={{ marginBottom: '16px' }}>
              <div 
                onClick={() => onSubjectChange(subj.name)}
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center', 
                  padding: '8px 0 12px 0', 
                  borderBottom: isActive ? '2px solid #2563EB' : '1px solid #D9E2EF',
                  marginBottom: '16px',
                  cursor: 'pointer'
                }}
              >
                <span style={{ fontSize: '13px', fontWeight: 700, color: isActive ? '#2563EB' : '#64748B' }}>
                  {subj.name} <span style={{ color: '#94A3B8', fontWeight: 600, fontSize: '11px', marginLeft: '4px' }}>({subj.count})</span>
                </span>
                {isActive ? <ChevronUp size={16} color="#2563EB" /> : <ChevronDown size={16} color="#94A3B8" />}
              </div>
              
              {isActive && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
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
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
