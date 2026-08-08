import { useState, useEffect, useCallback } from "react";
import type { SealedPaper } from "../../api/api";
import { useExamTimer } from "../../hooks/useExamTimer";
import { useConnectionStatus } from "../../hooks/useConnectionStatus";
import { useAutosave, type AutosavePayload } from "../../hooks/useAutosave";

import { ExamHeader } from "./ExamHeader";
import { QuestionPalette } from "./QuestionPalette";
import { QuestionCard } from "./QuestionCard";
import { ExamNavigation } from "./ExamNavigation";
import { SubjectTabs, Subject } from "./SubjectTabs";
import { QuestionInfo } from "./QuestionInfo";
import { SubmitConfirmation } from "./SubmitConfirmation";
import { calculateExamStats } from "../../utils/examStats";

interface Props {
  candidateId: string;
  paperHash: string;
  paper: SealedPaper;
  initialState: AutosavePayload | null;
  onSubmit: (answers: Record<number, number>) => void;
  startedAt: number;
  durationSeconds: number;
}

export function ExamClient({ candidateId, paperHash, paper, initialState, onSubmit, startedAt, durationSeconds }: Props) {
  const [current, setCurrent] = useState(initialState?.currentQuestion ?? 0);
  const [answers, setAnswers] = useState<Record<number, number>>(initialState?.answers ?? {});
  const [markedForReview, setMarkedForReview] = useState<Record<number, boolean>>(initialState?.markedForReview ?? {});
  const [visited, setVisited] = useState<Record<number, boolean>>({
    ...(initialState?.visited ?? {}),
    [initialState?.currentQuestion ?? 0]: true,
  });
  
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [hasLostFocus, setHasLostFocus] = useState(false);
  
  const question = paper.questions[current];
  const [activeSubject, setActiveSubject] = useState<Subject>(
    (question.subject.toUpperCase() as Subject) || "PHYSICS"
  );
  
  const stats = calculateExamStats(paper.questions.length, answers, markedForReview, visited);

  // Subject-specific stats
  const subjectQuestions = paper.questions.filter(q => q.subject.toUpperCase() === activeSubject);
  
  // Calculate local subject index
  const subjectQuestionIndex = subjectQuestions.findIndex(q => q.number === question.number);

  // Create a localized answers map for the subject stats
  const subjectAnswers: Record<number, number> = {};
  const subjectMarked: Record<number, boolean> = {};
  const subjectVisited: Record<number, boolean> = {};

  subjectQuestions.forEach((q, i) => {
    const globalIdx = q.number - 1;
    if (answers[q.number] !== undefined) subjectAnswers[q.number] = answers[q.number];
    if (markedForReview[q.number]) subjectMarked[q.number] = true;
    if (visited[globalIdx]) subjectVisited[i] = true; 
  });

  const subjectStats = calculateExamStats(subjectQuestions.length, subjectAnswers, subjectMarked, subjectVisited);

  const saveStatus = useAutosave(candidateId, {
    answers,
    markedForReview,
    visited,
    currentQuestion: current,
    paperHash,
  });

  const timer = useExamTimer(durationSeconds, startedAt);
  const connectionStatus = useConnectionStatus();

  // Auto-submit when time expires
  useEffect(() => {
    if (timer.isExpired) {
      onSubmit(answers);
    }
  }, [timer.isExpired, onSubmit, answers]);

  // Kiosk Mode Protections
  useEffect(() => {
    const handleContextMenu = (e: MouseEvent) => e.preventDefault();
    const handleCopyPaste = (e: ClipboardEvent) => e.preventDefault();
    const handleSelectStart = (e: Event) => e.preventDefault();
    
    const handleVisibilityChange = () => {
      if (document.hidden) setHasLostFocus(true);
    };
    const handleBlur = () => setHasLostFocus(true);
    const handleFocus = () => setHasLostFocus(false);

    document.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('copy', handleCopyPaste);
    document.addEventListener('cut', handleCopyPaste);
    document.addEventListener('paste', handleCopyPaste);
    document.addEventListener('selectstart', handleSelectStart);
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('copy', handleCopyPaste);
      document.removeEventListener('cut', handleCopyPaste);
      document.removeEventListener('paste', handleCopyPaste);
      document.removeEventListener('selectstart', handleSelectStart);
      
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  const toggleReview = useCallback(() => {
    setMarkedForReview((prev) => ({
      ...prev,
      [question.number]: !prev[question.number]
    }));
  }, [question.number]);

  const handleAnswer = useCallback((optionIndex: number) => {
    setAnswers((prev) => ({ ...prev, [question.number]: optionIndex }));
  }, [question.number]);

  const clearResponse = useCallback(() => {
    setAnswers((prev) => {
      const newAnswers = { ...prev };
      delete newAnswers[question.number];
      return newAnswers;
    });
  }, [question.number]);

  const handleQuestionSelect = (index: number) => {
    setCurrent(index);
    setVisited(prev => ({ ...prev, [index]: true }));
    setActiveSubject(paper.questions[index].subject.toUpperCase() as Subject);
  };

  const goPrevious = useCallback(() => {
    const prevIndex = Math.max(0, current - 1);
    setCurrent(prevIndex);
    setVisited(prev => ({ ...prev, [prevIndex]: true }));
    setActiveSubject(paper.questions[prevIndex].subject.toUpperCase() as Subject);
  }, [current, paper.questions]);

  const goNext = useCallback(() => {
    const nextIndex = Math.min(paper.questions.length - 1, current + 1);
    setCurrent(nextIndex);
    setVisited(prev => ({ ...prev, [nextIndex]: true }));
    setActiveSubject(paper.questions[nextIndex].subject.toUpperCase() as Subject);
  }, [current, paper.questions]);

  const handleSubjectChange = (subject: Subject) => {
    setActiveSubject(subject);
    
    // Find the first unvisited question in this subject, or default to the first question in the subject
    const subjQs = paper.questions.filter(q => q.subject.toUpperCase() === subject);
    if (subjQs.length === 0) return;

    let targetGlobalIndex = subjQs[0].number - 1;
    for (const q of subjQs) {
      const gIdx = q.number - 1;
      if (!visited[gIdx] && answers[q.number] === undefined) {
        targetGlobalIndex = gIdx;
        break;
      }
    }
    
    setCurrent(targetGlobalIndex);
    setVisited(prev => ({ ...prev, [targetGlobalIndex]: true }));
  };

  return (
    <div className="cbt-layout">
      {hasLostFocus && (
        <div className="modal-overlay kiosk-warning">
          <div className="modal-content card" style={{ borderColor: 'var(--warning)', borderTopWidth: '4px', textAlign: 'center', maxWidth: '450px' }}>
            <h2 className="text-text" style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>EXAM WINDOW FOCUS LOST</h2>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>Please return to the examination window.<br/>Your exam session remains active.</p>
            <button className="btn btn-primary primary" style={{ width: '100%' }} onClick={() => setHasLostFocus(false)}>Return to Examination</button>
          </div>
        </div>
      )}

      {showSubmitConfirm && (
        <SubmitConfirmation
          stats={stats}
          onConfirm={() => onSubmit(answers)}
          onCancel={() => setShowSubmitConfirm(false)}
        />
      )}

      <ExamHeader
        examName="National Eligibility cum Entrance Test (NEET)"
        candidateId={candidateId}
        candidateName="Aarav Sharma"
        connectionStatus={connectionStatus}
        saveStatus={saveStatus}
        timer={timer}
      />

      <div className="cbt-main-wrapper">
        <QuestionPalette
          questions={paper.questions}
          currentQuestionIndex={current}
          answers={answers}
          markedForReview={markedForReview}
          visited={visited}
          onQuestionSelect={handleQuestionSelect}
          activeSubject={activeSubject}
          overallStats={stats}
        />

        <div className="cbt-main-center">
          <SubjectTabs activeSubject={activeSubject} onSubjectChange={handleSubjectChange} />
          <div className="cbt-content">
            <QuestionCard
              question={question}
              subjectQuestionsCount={subjectQuestions.length}
              subjectQuestionIndex={subjectQuestionIndex}
              selectedAnswer={answers[question.number]}
              onAnswerSelect={handleAnswer}
              onMarkReview={toggleReview}
            />
          </div>
          <ExamNavigation
            onPrevious={goPrevious}
            onNext={goNext}
            onMarkReview={toggleReview}
            onClearResponse={clearResponse}
            onSubmit={() => setShowSubmitConfirm(true)}
            isFirst={current === 0}
            isLast={current === paper.questions.length - 1}
            isMarked={!!markedForReview[question.number]}
            hasAnswer={answers[question.number] !== undefined}
          />
        </div>

        <QuestionInfo question={question} subjectStats={subjectStats} />
      </div>
    </div>
  );
}
