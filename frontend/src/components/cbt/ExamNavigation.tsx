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
    <div className="cbt-navigation">
      
      {/* LEFT */}
      <div className="nav-group-left" style={{ display: 'flex', gap: '12px', flex: '1 1 auto' }}>
        <button 
          className="secondary" 
          onClick={onPrevious} 
          disabled={isFirst}
        >
          <ArrowLeft size={16} /> Previous
        </button>
      </div>

      {/* CENTER */}
      <div className="nav-group-center" style={{ display: 'flex', gap: '12px', flex: '1 1 auto', justifyContent: 'center', flexWrap: 'wrap' }}>
        <button 
          className="secondary" 
          onClick={onClearResponse}
          disabled={!hasAnswer}
        >
          <XCircle size={16} /> Clear Response
        </button>
        <button 
          className="secondary" 
          onClick={onMarkReview}
          style={{ borderColor: isMarked ? 'var(--warning)' : undefined, color: isMarked ? 'var(--warning)' : undefined }}
        >
          <Bookmark size={16} fill={isMarked ? "var(--warning)" : "none"} /> 
          {isMarked ? "Unmark Review" : "Mark for Review"}
        </button>
      </div>

      {/* RIGHT */}
      <div className="nav-group-right" style={{ display: 'flex', gap: '12px', flex: '1 1 auto', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
        <button 
          className="btn-outline-primary" 
          onClick={onNext} 
          disabled={isLast}
        >
          Save & Next <ArrowRight size={16} />
        </button>
        {isLast && (
          <button 
            className="btn-primary primary" 
            onClick={onSubmit}
          >
            Submit Test <Send size={16} />
          </button>
        )}
      </div>

    </div>
  );
}
