import { useState } from "react";
import { api, type IssuedPaper, type Receipt, type ResponseEvent } from "./api";
import { ExamClient } from "./components/ExamClient";
import { ReceiptCard } from "./components/ReceiptCard";
import { hashResponseInitial, hashResponseStep } from "./crypto";

type Stage = "checkin" | "exam" | "done";

export default function App() {
  const [stage, setStage] = useState<Stage>("checkin");
  const [candidateId, setCandidateId] = useState("NEET2026-000123");
  const [sessionId] = useState("2026-NEET-UG");
  const [issued, setIssued] = useState<IssuedPaper | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [events, setEvents] = useState<ResponseEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Actually, computing from events is a bit tricky if we only have item_id in event.
  // We can just keep a parallel `answers` state for the UI.
  const [answers, setAnswers] = useState<Record<number, number>>({});

  async function checkIn() {
    setBusy(true);
    setError(null);
    try {
      await api.checkIn(candidateId, sessionId);
      const paper = await api.issuePaper(candidateId, sessionId);
      setIssued(paper);
      setStage("exam");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  function handleAnswer(question_id: string, question_num: number, option_index: number) {
    const timestamp_iso = new Date().toISOString();
    setEvents((prev) => [...prev, { question_id, selected_option_index: option_index, timestamp_iso }]);
    setAnswers((prev) => ({ ...prev, [question_num]: option_index }));
  }

  async function submit() {
    if (!issued) return;
    setBusy(true);
    try {
      let chainDigest = await hashResponseInitial(issued.paper_hash);
      for (const event of events) {
        chainDigest = await hashResponseStep(chainDigest, event);
      }
      
      const response = await api.submitExam(candidateId, sessionId, events, chainDigest);
      setReceipt(response.receipt);
      setStage("done");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <header>
        <h1>
          NETI <span className="muted">— Non-Exploitable Test Integrity</span>
        </h1>
        {issued && (
          <p className="muted small">
            Session: {sessionId} · Bank: {issued.paper.bank_version} · Blueprint: {issued.paper.blueprint}
          </p>
        )}
      </header>

      {error && <p className="error">{error}</p>}

      {stage === "checkin" && (
        <section className="card">
          <h2>Candidate check-in</h2>
          <p className="muted">
            Your paper does not exist yet. It is generated when you check in.
            (Ensure the bank is unlocked before proceeding!)
          </p>
          <label className="field">
            Roll number
            <input value={candidateId} onChange={(e) => setCandidateId(e.target.value)} />
          </label>
          <button className="primary" onClick={checkIn} disabled={busy || !candidateId}>
            {busy ? "Generating…" : "Check in and generate my paper"}
          </button>
        </section>
      )}

      {stage === "exam" && issued && (
        <>
          <p className="muted small mono">
            paper {issued.paper_hash.slice(0, 32)}…
          </p>
          <ExamClient
            paper={issued.paper}
            answers={answers}
            onAnswer={handleAnswer}
            onSubmit={submit}
          />
        </>
      )}

      {stage === "done" && receipt && issued && (
        <ReceiptCard receipt={receipt} paperHash={issued.paper_hash} />
      )}
    </main>
  );
}
