import { useState, useEffect, useCallback } from "react";
import type { SealedPaper } from "../../api/api";
import { useServerTimer } from "../../hooks/useServerTimer";
import { useConnectionStatus } from "../../hooks/useConnectionStatus";
import { useAutosave, type AutosavePayload } from "../../hooks/useAutosave";
import { useTabOwnership } from "../../hooks/useTabOwnership";
import { useExamSecurity } from "../../hooks/useExamSecurity";

import { ExamHeader } from "./ExamHeader";
import { QuestionPalette } from "./QuestionPalette";
import { QuestionCard } from "./QuestionCard";
import { ExamNavigation } from "./ExamNavigation";
import { SubjectTabs, Subject } from "./SubjectTabs";
import { QuestionInfo } from "./QuestionInfo";
import { SubmitConfirmation } from "./SubmitConfirmation";
import { calculateExamStats } from "../../utils/examStats";

export function getDisplaySubject(rawSubject: string): Subject {
  const upper = rawSubject.toUpperCase();
  if (upper === "BOTANY" || upper === "ZOOLOGY") return "BIOLOGY";
  return upper as Subject;
}

interface Props {
  candidateId: string;
  paperHash: string;
  paper: SealedPaper;
  initialState: AutosavePayload | null;
  onSubmit: (events: any[], expectedResponseChain: string) => void;
  expiresAtIso?: string;
  fallbackDurationSeconds: number;
  fallbackStartTimeMs: number;
}

export function ExamClient({ candidateId, paperHash, paper, initialState, onSubmit, expiresAtIso, fallbackDurationSeconds, fallbackStartTimeMs }: Props) {
  // Navigation index (0 to 179)
  const [current, setCurrent] = useState(0);
  
  // Update state tracking to use item_id as canonical identity
  const [answers, setAnswers] = useState<Record<string, number>>(initialState?.answers ?? {});
  const [markedForReview, setMarkedForReview] = useState<Record<string, boolean>>(initialState?.markedForReview ?? {});
  
  // Set current and initially visit the appropriate question
  useEffect(() => {
    if (initialState?.currentQuestionId) {
      const idx = paper.questions.findIndex(q => q.item_id === initialState.currentQuestionId);
      if (idx !== -1) setCurrent(idx);
    }
  }, [initialState?.currentQuestionId, paper.questions]);

  const [visited, setVisited] = useState<Record<string, boolean>>(() => {
    const initialVisited = initialState?.visited ?? {};
    const startId = initialState?.currentQuestionId ?? paper.questions[0]?.item_id;
    if (startId) initialVisited[startId] = true;
    return initialVisited;
  });
  
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  
  const question = paper.questions[current];
  const [activeSubject, setActiveSubject] = useState<Subject>(
    getDisplaySubject(question.subject)
  );
  
  const stats = calculateExamStats(paper.questions, answers, markedForReview, visited);

  // Subject-specific stats
  const subjectQuestions = paper.questions.filter(q => getDisplaySubject(q.subject) === activeSubject);
  const subjectQuestionIndex = subjectQuestions.findIndex(q => q.item_id === question.item_id);

  const subjectStats = calculateExamStats(subjectQuestions, answers, markedForReview, visited);

  const { status: saveStatus, addAnswerEvent, getEvents, getExpectedChain } = useAutosave(candidateId, {
    answers,
    markedForReview,
    visited,
    currentQuestionId: question.item_id,
    paperHash,
    fallbackStartTimeMs,
  });

  const timer = useServerTimer(expiresAtIso, fallbackDurationSeconds, fallbackStartTimeMs);
  const connectionStatus = useConnectionStatus();
  
  // Hardened Multi-Tab prevention using heartbeat
  const isOwner = useTabOwnership(paperHash);

  // Auto-submit when time expires
  useEffect(() => {
    if (timer.isExpired) {
      onSubmit(getEvents(), getExpectedChain());
    }
  }, [timer.isExpired, onSubmit, getEvents, getExpectedChain]);

  const { hasLostFocus, clearFocusLoss, enterFullscreen } = useExamSecurity();

  // Kiosk Mode Protections (now managed via useExamSecurity hook)

  const toggleReview = useCallback(() => {
    setMarkedForReview((prev) => ({
      ...prev,
      [question.item_id]: !prev[question.item_id]
    }));
  }, [question.item_id]);

  const handleAnswer = useCallback((optionIndex: number) => {
    setAnswers((prev) => ({ ...prev, [question.item_id]: optionIndex }));
    addAnswerEvent(question.item_id, optionIndex);
  }, [question.item_id, addAnswerEvent]);

  const clearResponse = useCallback(() => {
    setAnswers((prev) => {
      const newAnswers = { ...prev };
      delete newAnswers[question.item_id];
      return newAnswers;
    });
  }, [question.item_id]);

  const handleQuestionSelect = (index: number) => {
    const targetQ = paper.questions[index];
    setCurrent(index);
    setVisited(prev => ({ ...prev, [targetQ.item_id]: true }));
    setActiveSubject(getDisplaySubject(targetQ.subject));
  };

  const goPrevious = useCallback(() => {
    const prevIndex = Math.max(0, current - 1);
    const targetQ = paper.questions[prevIndex];
    setCurrent(prevIndex);
    setVisited(prev => ({ ...prev, [targetQ.item_id]: true }));
    setActiveSubject(getDisplaySubject(targetQ.subject));
  }, [current, paper.questions]);

  const goNext = useCallback(() => {
    const nextIndex = Math.min(paper.questions.length - 1, current + 1);
    const targetQ = paper.questions[nextIndex];
    setCurrent(nextIndex);
    setVisited(prev => ({ ...prev, [targetQ.item_id]: true }));
    setActiveSubject(getDisplaySubject(targetQ.subject));
  }, [current, paper.questions]);

  const handleSubjectChange = (subject: Subject) => {
    setActiveSubject(subject);
    
    // Find the first unvisited question in this subject, or default to the first question in the subject
    const subjQs = paper.questions.filter(q => getDisplaySubject(q.subject) === subject);
    if (subjQs.length === 0) return;

    let targetGlobalIndex = paper.questions.findIndex(q => q.item_id === subjQs[0].item_id);
    for (const q of subjQs) {
      if (!visited[q.item_id] && answers[q.item_id] === undefined) {
        targetGlobalIndex = paper.questions.findIndex(allQ => allQ.item_id === q.item_id);
        break;
      }
    }
    
    const targetQ = paper.questions[targetGlobalIndex];
    setCurrent(targetGlobalIndex);
    setVisited(prev => ({ ...prev, [targetQ.item_id]: true }));
  };

  return (
    <div className="cbt-layout">
      {!isOwner && (
        <div className="modal-overlay" style={{ zIndex: 9999, background: '#fff', color: '#111' }}>
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <h1 style={{ color: '#DC2626' }}>Multiple Tabs Detected</h1>
            <p style={{ fontSize: '1.25rem', marginTop: '1rem' }}>This examination session is already open in another tab.</p>
            <p style={{ marginTop: '0.5rem', color: '#666' }}>Please return to the original tab to continue your examination.</p>
          </div>
        </div>
      )}

      {hasLostFocus && isOwner && (
        <div className="modal-overlay kiosk-warning" role="dialog" aria-modal="true" aria-labelledby="focus-loss-heading">
          <div className="modal-content card" style={{ borderColor: 'var(--warning)', borderTopWidth: '4px', textAlign: 'center', maxWidth: '450px' }}>
            <h2 id="focus-loss-heading" className="text-text" style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Exam window lost focus</h2>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>Please return to the examination window to continue your exam.</p>
            <button className="btn btn-primary primary" style={{ width: '100%' }} onClick={clearFocusLoss} autoFocus>Return to Exam</button>
          </div>
        </div>
      )}

      {showSubmitConfirm && (
        <SubmitConfirmation
          stats={stats}
          onConfirm={() => onSubmit(getEvents(), getExpectedChain())}
          onCancel={() => setShowSubmitConfirm(false)}
        />
      )}

      <ExamHeader
        candidateId={candidateId}
        connectionStatus={connectionStatus}
        saveStatus={saveStatus}
        timer={timer}
        onSubmit={() => setShowSubmitConfirm(true)}
        onRequestFullscreen={enterFullscreen}
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
          onSubjectChange={handleSubjectChange}
          overallStats={stats}
        />

        <div className="cbt-main-center">
          <SubjectTabs activeSubject={activeSubject} onSubjectChange={handleSubjectChange} />
          <div className="cbt-content">
            <QuestionCard 
              question={question} 
              subjectQuestionsCount={subjectQuestions.length}
              subjectQuestionIndex={subjectQuestionIndex}
              selectedAnswer={answers[question.item_id]}
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
            isMarked={!!markedForReview[question.item_id]}
            hasAnswer={answers[question.item_id] !== undefined}
          />
        </div>

        <QuestionInfo question={question} subjectStats={subjectStats} />
      </div>
    </div>
  );
}
