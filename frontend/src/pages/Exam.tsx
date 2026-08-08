import { useLocation, Navigate, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ExamClient } from "../components/cbt/ExamClient";
import { IssuedPaperMock, SessionInfoMock } from "../api/api-mocks";
import { api } from "../api/api";
import { AutosavePayload } from "../hooks/useAutosave";

export function Exam() {
  const location = useLocation();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const state = location.state as { 
    paper: IssuedPaperMock, 
    session: SessionInfoMock,
    candidateId: string,
    restoredState: AutosavePayload | null
  } | null;

  if (!state || !state.paper) {
    return <Navigate to="/checkin" replace />;
  }

  const { paper, session, candidateId, restoredState } = state;

  async function submit(finalAnswers: Record<number, number>) {
    setBusy(true);
    try {
      // POST answers -> get receipt
      const receipt = await api.receipt(paper.leaf_index);
      navigate("/receipt", { state: { receipt, paperHash: paper.paper_hash } });
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p className="muted small mono">
        paper {paper.paper_hash.slice(0, 32)}… · ledger #{paper.leaf_index}
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
