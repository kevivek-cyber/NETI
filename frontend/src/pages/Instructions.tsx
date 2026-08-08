import { useState } from "react";
import { useLocation, Navigate, useNavigate } from "react-router-dom";
import { IssuedPaperMock, SessionInfoMock } from "../api/api-mocks";
import { AutosavePayload } from "../hooks/useAutosave";
import { motion } from "framer-motion";
import { Info, Navigation, ShieldAlert, CheckSquare } from "lucide-react";

export function Instructions() {
  const location = useLocation();
  const navigate = useNavigate();
  const [acknowledged, setAcknowledged] = useState(false);

  const state = location.state as { 
    paper: IssuedPaperMock, 
    session: SessionInfoMock,
    candidateId: string,
    restoredState: AutosavePayload | null,
    candidate: any
  } | null;

  if (!state || !state.paper) {
    return <Navigate to="/checkin" replace />;
  }

  const { session, candidateId, candidate } = state;

  return (
    <>
      <header className="cbt-header" style={{ marginBottom: '2rem' }}>
        <div className="cbt-header-brand">
          <h1 className="cbt-header-title">NETI</h1>
          <span className="cbt-header-subtitle">| {candidate.examName}</span>
        </div>
      </header>

      <main style={{ maxWidth: '1000px' }}>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
            <div style={{ background: '#F1F5F9', padding: '1.5rem 2rem', borderBottom: '1px solid var(--border)' }}>
              <h2 style={{ color: 'var(--text)', margin: 0, fontSize: '1.4rem' }}>Examination Instructions</h2>
              <p className="muted" style={{ margin: '0.2rem 0 0' }}>Please read the following instructions carefully before starting your exam.</p>
            </div>

            <div style={{ padding: '2rem' }}>
              <section className="instructions-section">
                <h3><Info size={18} style={{ verticalAlign: 'text-bottom', marginRight: '0.5rem' }}/> 1. EXAM INFORMATION</h3>
                <div style={{ background: '#F8FAFC', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1.25rem', marginBottom: '1.5rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                  <div>
                    <div className="muted small" style={{ fontWeight: 600 }}>CANDIDATE</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{candidate.name} ({candidateId})</div>
                  </div>
                  <div>
                    <div className="muted small" style={{ fontWeight: 600 }}>DURATION</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{session.duration_seconds / 60} Minutes</div>
                  </div>
                  <div>
                    <div className="muted small" style={{ fontWeight: 600 }}>TOTAL QUESTIONS</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{session.questions}</div>
                  </div>
                </div>
              </section>

              <section className="instructions-section">
                <h3><Navigation size={18} style={{ verticalAlign: 'text-bottom', marginRight: '0.5rem' }}/> 2. NAVIGATION & STATUS</h3>
                <ul className="instructions-list">
                  <li>Use the <strong>Save & Next</strong> button to save your answer and move to the next question.</li>
                  <li>Use the <strong>Mark for Review</strong> button to flag a question. This helps you quickly identify questions you want to revisit later.</li>
                  <li>Use the <strong>Question Palette</strong> on the right to jump directly to any question.</li>
                </ul>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: '#F8FAFC', padding: '1.25rem', border: '1px solid var(--border)', borderRadius: 'var(--radius)', marginTop: '1rem' }}>
                  <div className="legend-item"><span className="chip-not-visited legend-chip"></span> Not Visited</div>
                  <div className="legend-item"><span className="chip-not-answered legend-chip"></span> Not Answered</div>
                  <div className="legend-item"><span className="chip-answered legend-chip"></span> Answered</div>
                  <div className="legend-item"><span className="chip-review legend-chip"></span> Marked for Review</div>
                  <div className="legend-item" style={{ gridColumn: 'span 2' }}><span className="chip-answered-review legend-chip"></span> Answered & Marked for Review (will be evaluated)</div>
                </div>
              </section>

              <section className="instructions-section">
                <h3><ShieldAlert size={18} style={{ verticalAlign: 'text-bottom', marginRight: '0.5rem' }}/> 3. SECURITY & SYSTEM</h3>
                <ul className="instructions-list">
                  <li><strong>Focus Monitoring:</strong> Navigating away from the examination window will trigger a security warning.</li>
                  <li><strong>Autosave:</strong> Your answers are saved automatically locally and synchronized with the server. Even in the event of network loss, your data remains safe.</li>
                  <li><strong>Network Disconnection:</strong> If the connection to the server is lost, an Offline indicator will appear. You can continue answering; data will sync when the connection restores.</li>
                  <li><strong>Submission:</strong> The exam will auto-submit when the timer reaches zero. You may submit early using the Submit Exam button.</li>
                </ul>
              </section>

              <div style={{ padding: '1.5rem', background: '#F1F5F9', borderRadius: 'var(--radius)', border: '1px solid var(--border)', marginBottom: '2rem' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer', fontSize: '1.1rem', fontWeight: 600 }}>
                  <input 
                    type="checkbox" 
                    checked={acknowledged} 
                    onChange={(e) => setAcknowledged(e.target.checked)} 
                    style={{ width: '1.5rem', height: '1.5rem', accentColor: 'var(--primary)' }}
                  />
                  I have read and understood all the examination instructions.
                </label>
              </div>

              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', paddingTop: '1.5rem', borderTop: '1px solid var(--border)' }}>
                <button className="secondary" onClick={() => navigate("/checkin")}>
                  Back to Check-in
                </button>
                <button 
                  className="primary"
                  disabled={!acknowledged} 
                  onClick={() => navigate("/exam", { state })}
                  style={{ minWidth: '200px' }}
                >
                  Start Examination <CheckSquare size={18} style={{ marginLeft: '0.5rem' }}/>
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </main>
    </>
  );
}
