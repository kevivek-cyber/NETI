import { useLocation, Navigate } from "react-router-dom";
import { useState } from "react";
import { ExamClient } from "../components/cbt/ExamClient";
import { IssuedPaperMock, SessionInfoMock } from "../api/api-mocks";
import { AutosavePayload } from "../hooks/useAutosave";

export function Exam() {
  const location = useLocation();
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
      // TODO(role 4): wire this to api.submitExam once ExamClient tracks a
      // timestamped event log (question_id, selected_option_index,
      // timestamp_iso) for every answer change, not just the final
      // snapshot in `finalAnswers` — and once a client-side implementation
      // of the response-chain hashing (INTEGRITY.md §8, matching
      // backend/app/ledger/canonical.py + hashing.py byte-for-byte) exists
      // to fold that log into `expected_response_chain`. See the TODO at
      // the bottom of api.ts for why that hashing can't be stubbed.
      //
      // The previous version of this function called `api.receipt(...)`,
      // a method that never existed on the real backend and, even as a
      // stub, never sent `finalAnswers` anywhere — it silently discarded
      // the candidate's answers instead of submitting them. Left failing
      // loudly instead of silently, until the pieces above exist.
      // (Re-add `useNavigate` and navigate to "/receipt" with the real
      // receipt on success once this actually calls api.submitExam.)
      throw new Error(
        "Exam submission is not wired to the backend yet — see the TODO in Exam.tsx"
      );
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
