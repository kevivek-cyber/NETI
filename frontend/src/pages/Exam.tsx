import { useLocation, Navigate, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { ExamClient } from "../components/cbt/ExamClient";
import { api, SubmitRequest, ResponseEvent } from "../api/api";
import { AutosavePayload, restoreSession } from "../hooks/useAutosave";
import { clearSessionData } from "../utils/storage";

export function Exam() {
  const location = useLocation();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestRestoredState, setLatestRestoredState] = useState<AutosavePayload | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const state = location.state as { 
    paper: any;
    session: any;
    candidateId: string,
    restoredState: AutosavePayload | null,
    fallbackStartTimeMs: number
  } | null;

  useEffect(() => {
    if (!state || !state.paper) return;
    
    let mounted = true;

    // 1. Check authoritative backend state before restoring
    api.checkIn({ candidate_id: state.candidateId, session_id: state.session.session_id })
      .then((res) => {
        if (!mounted) return;
        
        if (res.session_state === "submitted") {
          navigate("/checkin", { replace: true });
          return;
        }

        // 2. If not submitted, load IndexedDB
        restoreSession(state.candidateId).then((saved) => {
          if (!mounted) return;
          if (saved && saved.paperHash === state.paper.paper_hash) {
            setLatestRestoredState(saved);
          } else {
            setLatestRestoredState(state.restoredState);
          }
          setIsInitializing(false);
        });
      })
      .catch((err) => {
        if (!mounted) return;
        if (err.message && err.message.includes("SESSION_ALREADY_SUBMITTED")) {
          navigate("/checkin", { replace: true });
          return;
        }
        
        // Fallback for network offline: continue to load
        restoreSession(state.candidateId).then((saved) => {
          if (!mounted) return;
          if (saved && saved.paperHash === state.paper.paper_hash) {
            setLatestRestoredState(saved);
          } else {
            setLatestRestoredState(state.restoredState);
          }
          setIsInitializing(false);
        });
      });

    return () => { mounted = false; };
  }, [state, navigate]);

  if (!state || !state.paper) {
    return <Navigate to="/checkin" replace />;
  }

  const { paper, session, candidateId, fallbackStartTimeMs } = state;

  async function submit(events: ResponseEvent[], expectedResponseChain: string) {
    setBusy(true);
    try {
      const payload: SubmitRequest = {
        candidate_id: candidateId,
        session_id: session.session_id,
        events,
        expected_response_chain: expectedResponseChain,
      };
      const res = await api.submitExam(payload);
      
      // Clear local IndexedDB snapshot strictly ON SUCCESS
      await clearSessionData(`session_${candidateId}`);

      navigate("/receipt", { state: { receipt: res.receipt, paperHash: paper.paper_hash }, replace: true });
    } catch (e: any) {
      if (e.message && e.message.includes("SESSION_ALREADY_SUBMITTED")) {
         await clearSessionData(`session_${candidateId}`);
         navigate("/checkin", { replace: true });
         return;
      }
      setError("Submission could not be confirmed. Your responses are saved locally. Please reconnect or contact the invigilator.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p className="muted small mono" style={{ display: "none" }}>
        {/* Intentionally hidden for a cleaner UI, but retained for debug */}
        paper {paper.paper_hash.slice(0, 32)}…
      </p>
      {error && <p className="error">{error}</p>}
      {isInitializing ? (
        <p>Restoring exam session...</p>
      ) : busy ? (
        <p>Submitting exam...</p>
      ) : (
        <ExamClient
          candidateId={candidateId}
          paperHash={paper.paper_hash}
          paper={paper.paper}
          initialState={latestRestoredState}
          onSubmit={submit}
          expiresAtIso={session.expires_at_iso}
          fallbackDurationSeconds={session.duration_seconds}
          fallbackStartTimeMs={fallbackStartTimeMs}
        />
      )}
    </>
  );
}
