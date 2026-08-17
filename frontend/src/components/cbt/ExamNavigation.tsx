import { ArrowLeft, ArrowRight, Bookmark, XCircle, Send } from "lucide-react";

interface ExamNavigationProps {
  onPrevious: () => void;
  onNext: () => void;
  onMarkReview: () => void;
  onClearResponse: () => void;
  onSubmit: () => void;
  isFirst: boolean;
  isLast: boolean;
  isMarked: boolean;
  hasAnswer: boolean;
}

const css = `
  .nav-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    height: 48px;
    padding: 0 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    font-family: '"Inter", sans-serif';
  }
  .nav-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .nav-btn-neutral {
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    color: #475569;
  }
  .nav-btn-neutral:hover:not(:disabled) {
    background: #F8FAFC;
    border-color: #94A3B8;
  }
  
  .nav-btn-outline-purple {
    background: #FFFFFF;
    border: 1px solid #C4B5FD;
    color: #8B5CF6;
  }
  .nav-btn-outline-purple:hover:not(:disabled) {
    background: #F5F3FF;
  }
  .nav-btn-outline-purple.active {
    background: #F5F3FF;
    border-color: #8B5CF6;
  }
  
  .nav-btn-primary {
    background: #2563EB;
    border: 1px solid #2563EB;
    color: #FFFFFF;
    box-shadow: 0 2px 4px rgba(37,99,235,0.2);
  }
  .nav-btn-primary:hover:not(:disabled) {
    background: #1D4ED8;
    border-color: #1D4ED8;
  }

  .nav-btn-submit {
    background: #16A34A;
    border: 1px solid #16A34A;
    color: #FFFFFF;
    box-shadow: 0 2px 4px rgba(22,163,74,0.2);
  }
  .nav-btn-submit:hover:not(:disabled) {
    background: #15803D;
    border-color: #15803D;
  }
`;

export function ExamNavigation({
  onPrevious,
  onNext,
  onMarkReview,
  onClearResponse,
  onSubmit,
  isFirst,
  isLast,
  isMarked,
  hasAnswer,
}: ExamNavigationProps) {
  return (
    <div style={{ 
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 24px',
      background: '#FFFFFF',
      borderTop: '1px solid #D9E2EF',
      boxShadow: '0 -4px 12px rgba(23,42,70,0.03)',
      position: 'sticky',
      bottom: 0,
      zIndex: 100
    }}>
      <style>{css}</style>

      {/* LEFT */}
      <div>
        <button 
          className="nav-btn nav-btn-neutral" 
          onClick={onPrevious} 
          disabled={isFirst}
        >
          <ArrowLeft size={18} /> Previous
        </button>
      </div>

      {/* CENTER */}
      <div style={{ display: 'flex', gap: '16px' }}>
        <button 
          className="nav-btn nav-btn-neutral" 
          onClick={onClearResponse}
          disabled={!hasAnswer}
        >
          <XCircle size={18} /> Clear Response
        </button>
        <button 
          className={`nav-btn nav-btn-outline-purple ${isMarked ? 'active' : ''}`}
          onClick={onMarkReview}
        >
          <Bookmark size={18} fill={isMarked ? "#8B5CF6" : "none"} /> 
          {isMarked ? "Unmark Review" : "Mark for Review"}
        </button>
      </div>

      {/* RIGHT */}
      <div style={{ display: 'flex', gap: '16px' }}>
        <button 
          className="nav-btn nav-btn-primary" 
          onClick={onNext} 
          disabled={isLast}
        >
          Save & Next <ArrowRight size={18} />
        </button>
        {isLast && (
          <button 
            className="nav-btn nav-btn-submit" 
            onClick={onSubmit}
          >
            Submit Test <Send size={18} />
          </button>
        )}
      </div>

    </div>
  );
}
