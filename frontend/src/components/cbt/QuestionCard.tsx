import { Question } from "../../api/api";
import clsx from "clsx";
import { Info, CheckCircle2, Circle } from "lucide-react";

interface QuestionCardProps {
  question: Question;
  subjectQuestionsCount: number;
  subjectQuestionIndex: number;
  selectedAnswer?: number;
  onAnswerSelect: (index: number) => void;
  onMarkReview: () => void;
}

const css = `
  .q-opt-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 20px;
    border: 1px solid #D9E2EF;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    background: #FFFFFF;
    margin-bottom: 12px;
  }
  .q-opt-card:hover {
    background: #F5F8FC;
    border-color: #94A3B8;
  }
  .q-opt-card.selected {
    background: #EFF6FF;
    border-color: #2563EB;
    box-shadow: 0 0 0 1px #2563EB;
  }
  .q-opt-letter {
    font-weight: 700;
    color: #475569;
    font-size: 14px;
    width: 24px;
    flex-shrink: 0;
  }
  .q-opt-card.selected .q-opt-letter {
    color: #2563EB;
  }
  .q-opt-text {
    font-size: 15px;
    color: #172A46;
    flex: 1;
    word-wrap: break-word;
    font-weight: 500;
  }
`;

export function QuestionCard({
  question,
  subjectQuestionsCount,
  subjectQuestionIndex,
  selectedAnswer,
  onAnswerSelect,
  onMarkReview
}: QuestionCardProps) {
  const progressPercent = Math.round(((subjectQuestionIndex + 1) / subjectQuestionsCount) * 100);

  return (
    <div style={{ fontFamily: '"Inter", sans-serif' }}>
      <style>{css}</style>
      
      {/* Top Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
           <div style={{ fontSize: '13px', color: '#2563EB', fontWeight: 700, letterSpacing: '0.05em', marginBottom: '8px' }}>
             {question.subject.toUpperCase()}
           </div>
           <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#172A46', margin: '0 0 12px 0' }}>
             Question {subjectQuestionIndex + 1} of {subjectQuestionsCount}
           </h2>
           <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
             <div style={{ width: '200px', height: '6px', background: '#E2E8F0', borderRadius: '3px', overflow: 'hidden' }}>
               <div style={{ height: '100%', width: `${progressPercent}%`, background: '#2563EB', borderRadius: '3px' }}></div>
             </div>
             <span style={{ fontSize: '12px', color: '#64748B', fontWeight: 600 }}>{progressPercent}% Complete</span>
           </div>
        </div>
      </div>

      {/* Question Card */}
      <div style={{ background: '#FFFFFF', border: '1px solid #D9E2EF', borderRadius: '12px', padding: '24px', marginBottom: '32px', boxShadow: '0 1px 3px rgba(23,42,70,0.03)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#64748B', fontSize: '12px', fontWeight: 600, marginBottom: '16px' }}>
          <Info size={16} />
          <span>Overall Question No. {question.number}</span>
        </div>
        <p style={{ fontSize: '16px', lineHeight: 1.6, color: '#172A46', margin: 0, fontWeight: 500, wordWrap: 'break-word' }}>
          {question.stem}
        </p>
      </div>

      {/* Options */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {question.options.map((option: string, index: number) => {
          const isSelected = selectedAnswer === index;
          return (
            <label key={index} className={clsx("q-opt-card", isSelected && "selected")}>
              <input
                type="radio"
                name={`q-${question.number}`}
                checked={isSelected}
                onChange={() => onAnswerSelect(index)}
                style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }}
                aria-checked={isSelected}
              />
              <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {isSelected ? (
                  <CheckCircle2 size={24} color="#2563EB" fill="#EFF6FF" />
                ) : (
                  <Circle size={24} color="#CBD5E1" />
                )}
              </div>
              <span className="q-opt-letter">{"ABCD"[index]}</span>
              <span className="q-opt-text">{option}</span>
            </label>
          );
        })}
      </div>
      
    </div>
  );
}
