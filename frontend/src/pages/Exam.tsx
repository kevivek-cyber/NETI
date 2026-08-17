import { useLocation, Navigate, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ExamClient } from "../components/cbt/ExamClient";
import { api, SubmitRequest, ResponseEvent } from "../api/api";
import { AutosavePayload } from "../hooks/useAutosave";

export function Exam() {
  const location = useLocation();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const state = location.state as { 
    paper: any;
    session: any;
    candidateId: string,
    restoredState: AutosavePayload | null
  } | null;

  if (!state || !state.paper) {
    return <Navigate to="/checkin" replace />;
  }

  const { paper, session, candidateId, restoredState } = state;

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
      navigate("/receipt", { state: { receipt: res.receipt, paperHash: paper.paper_hash } });
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p className="muted small mono">
        paper {paper.paper_hash.slice(0, 32)}…
      </p>
      {error && <p className="error">{error}</p>}
      {busy ? (
        <p>Submitting exam...</p>
      ) : (
        <ExamClient
          candidateId={candidateId}
          paperHash={paper.paper_hash}
          paper={paper.paper}
          initialState={restoredState}
          onSubmit={submit}
          startedAt={paper.started_at}
          durationSeconds={session.duration_seconds}
        />
      )}
    </>
  );
}
