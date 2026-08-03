import { useState } from "react";
import { api, type IssuedPaper, type Receipt, type SessionInfo } from "./api";
import { ExamClient } from "./components/ExamClient";
import { ReceiptCard } from "./components/ReceiptCard";

type Stage = "checkin" | "exam" | "done";

export default function App() {
  const [stage, setStage] = useState<Stage>("checkin");
  const [candidateId, setCandidateId] = useState("NEET2026-000123");
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [issued, setIssued] = useState<IssuedPaper | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function checkIn() {
    setBusy(true);
    setError(null);
    try {
      // TODO(role 3): the ceremony is an invigilator action, not a
      // candidate one. Move it to the console app once that exists.
      setSession(await api.openSession("DEMO"));
      const paper = await api.issuePaper(candidateId);
      setIssued(paper);
      setStage("exam");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function submit() {
    if (!issued) return;
    setBusy(true);
    try {
      // TODO(role 3): POST the answers first; the server hashes them into
      // the response chain and returns a signed receipt.
      setReceipt(await api.receipt(issued.leaf_index));
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
        {session && (
          <p className="muted small">
            {session.blueprint} · {session.questions} questions · {session.marks} marks ·
            bank {session.bank_version}
          </p>
        )}
      </header>

      {error && <p className="error">{error}</p>}

      {stage === "checkin" && (
        <section className="card">
          <h2>Candidate check-in</h2>
          <p className="muted">
            Your paper does not exist yet. It is generated when you check in.
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
            paper {issued.paper_hash.slice(0, 32)}… · ledger #{issued.leaf_index}
          </p>
          <ExamClient
            paper={issued.paper}
            answers={answers}
            onAnswer={(q, o) => setAnswers((a) => ({ ...a, [q]: o }))}
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
