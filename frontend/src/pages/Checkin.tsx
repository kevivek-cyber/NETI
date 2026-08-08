import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiMocks } from "../api/api-mocks";

type CheckinState = "Ready" | "Checking in..." | "Generating paper..." | "Paper issued" | "Ready to start";

export function Checkin() {
  const [candidateId, setCandidateId] = useState("NEET2026-000123");
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<CheckinState>("Ready");
  const navigate = useNavigate();

  // Mock candidate details
  const candidate = {
    name: "Aarav Sharma",
    photoUrl: "https://i.pravatar.cc/150?u=a042581f4e29026704d",
    examName: "National Eligibility cum Entrance Test (NEET)",
    examCenter: "TCS iON Digital Zone, Mumbai",
    seatNumber: "A-42",
    examDate: new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' }),
    examStartTime: "10:00 AM",
    examDuration: "3 Hours",
  };

  async function checkIn() {
    setStatus("Checking in...");
    setError(null);
    try {
      await new Promise(r => setTimeout(r, 600)); 
      setStatus("Generating paper...");
      
      const session = await apiMocks.openSession("DEMO");
      const paper = await apiMocks.issuePaper(candidateId);
      
      setStatus("Paper issued");
      await new Promise(r => setTimeout(r, 400));
      
      const { restoreSession } = await import("../hooks/useAutosave");
      const savedSession = await restoreSession(candidateId);
      
      let restoredState = null;
      if (savedSession && savedSession.paperHash === paper.paper_hash) {
        restoredState = savedSession;
      }
      
      setStatus("Ready to start");
      await new Promise(r => setTimeout(r, 300));
      
      navigate("/instructions", { state: { paper, session, candidateId, restoredState, candidate } });
    } catch (e) {
      setError("An unexpected error occurred. Please try again.");
      console.error(e);
      setStatus("Ready");
    }
  }

  const isBusy = status !== "Ready";

  return (
    <>
      <header className="cbt-header" style={{ marginBottom: '2rem' }}>
        <div className="cbt-header-brand">
          <h1 className="cbt-header-title">NETI</h1>
          <span className="cbt-header-subtitle">| Check-in Portal</span>
        </div>
      </header>
      
      <main>
        {error && <p className="error">{error}</p>}
        <div className="card" style={{ maxWidth: '760px', margin: '0 auto', padding: '0', overflow: 'hidden' }}>
          
          <div style={{ background: '#F1F5F9', padding: '1.5rem', borderBottom: '1px solid var(--border)' }}>
            <h2 style={{ color: 'var(--primary)', margin: 0, fontSize: '1.25rem' }}>Candidate Verification</h2>
            <p className="muted small" style={{ margin: '0.2rem 0 0' }}>Please verify your details before proceeding to the instructions.</p>
          </div>

          <div style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '2.5rem' }}>
              <div style={{ flexShrink: 0 }}>
                <img 
                  src={candidate.photoUrl} 
                  alt="Candidate" 
                  style={{ width: 140, height: 160, objectFit: 'cover', border: '1px solid var(--border)', borderRadius: '4px', padding: '4px', background: '#fff' }} 
                />
              </div>
              
              <div style={{ flex: 1 }}>
                <dl className="receipt" style={{ margin: 0, gap: '0.75rem 1.5rem', gridTemplateColumns: '150px 1fr' }}>
                  <dt>Candidate Name:</dt>
                  <dd style={{ fontSize: '1.1rem', fontWeight: 600 }}>{candidate.name}</dd>
                  
                  <dt>Roll Number:</dt>
                  <dd className="mono" style={{ fontSize: '1.05rem', fontWeight: 600 }}>{candidateId}</dd>
                  
                  <dt>Examination:</dt>
                  <dd>{candidate.examName}</dd>
                  
                  <dt>Exam Center:</dt>
                  <dd>{candidate.examCenter}</dd>
                  
                  <dt>Seat Number:</dt>
                  <dd style={{ fontWeight: 600, color: 'var(--primary)' }}>{candidate.seatNumber}</dd>
                  
                  <dt>Date & Time:</dt>
                  <dd>{candidate.examDate} at {candidate.examStartTime}</dd>
                  
                  <dt>Duration:</dt>
                  <dd>{candidate.examDuration}</dd>
                </dl>
              </div>
            </div>

            <div style={{ background: '#F8FAFC', padding: '1.5rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <div className="field" style={{ margin: '0 0 1.5rem 0' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Confirm Roll Number</label>
                <input 
                  type="text"
                  value={candidateId} 
                  onChange={(e) => setCandidateId(e.target.value)} 
                  disabled={isBusy}
                  style={{ maxWidth: '300px' }}
                />
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border)', paddingTop: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span className="muted" style={{ fontWeight: 500, fontSize: '0.95rem' }}>System Status:</span>
                  <span style={{ 
                    fontWeight: 600, 
                    color: isBusy ? 'var(--primary)' : 'var(--text)',
                    backgroundColor: isBusy ? 'var(--primary-soft)' : 'transparent',
                    padding: isBusy ? '0.2rem 0.6rem' : '0',
                    borderRadius: '4px'
                  }}>
                    {status}
                  </span>
                </div>
                <button className="primary" style={{ padding: '0.75rem 1.5rem' }} onClick={checkIn} disabled={isBusy || !candidateId}>
                  Check In & Generate Paper
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
