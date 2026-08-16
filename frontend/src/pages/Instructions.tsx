import { useState, useEffect } from "react";
import { useLocation, Navigate, useNavigate } from "react-router-dom";
import { AutosavePayload } from "../hooks/useAutosave";
import { motion } from "framer-motion";
import { 
  Info, 
  Navigation, 
  ArrowRight,
  Shield,
  MonitorOff,
  WifiOff,
  AlertTriangle,
  RefreshCw
} from "lucide-react";
import { examConfig } from "../config/examConfig";

const css = `
  .card-shadow {
    box-shadow: 0px 4px 20px rgba(11, 35, 69, 0.04);
  }
`;

export function Instructions() {
  const location = useLocation();
  const navigate = useNavigate();
  const [acknowledged, setAcknowledged] = useState(false);

  // Scroll to top on mount
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const state = location.state as { 
    paper: any, 
    session: any,
    candidateId: string,
    restoredState: AutosavePayload | null,
    fallbackStartTimeMs: number
  } | null;

  if (!state || !state.paper) {
    return <Navigate to="/checkin" replace />;
  }

  const { candidateId } = state;

  return (
    <>
      <style>{css}</style>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} style={{ fontFamily: '"Inter", sans-serif', paddingBottom: '80px' }}>
        
        {/* Page Hero */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h2 style={{ fontSize: '32px', color: '#0F172A', fontWeight: 700, margin: '0 0 12px 0', letterSpacing: '-0.02em' }}>
            Examination Instructions
          </h2>
          <p style={{ color: '#64748B', fontSize: '15px', margin: '0 0 24px 0', fontWeight: 500 }}>
            Please review the following information carefully before starting your examination.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', fontSize: '13px', fontWeight: 600 }}>
            <span style={{ color: '#0F172A' }}>01 Exam Information</span> <ArrowRight size={14} color="#CBD5E1"/>
            <span style={{ color: '#0F172A' }}>02 Navigation</span> <ArrowRight size={14} color="#CBD5E1"/>
            <span style={{ color: '#0F172A' }}>03 Security</span> <ArrowRight size={14} color="#CBD5E1"/>
            <span style={{ color: '#2563EB' }}>04 Ready</span>
          </div>
        </div>

        {/* Exam Information Card */}
        <div className="card-shadow" style={{ background: '#FFF', borderRadius: '12px', border: '1px solid #E2E8F0', padding: '32px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '4px' }}>
             <Info size={24} color="#2563EB" />
             <h3 style={{ margin: 0, fontSize: '18px', color: '#0F172A', fontWeight: 700 }}>Exam Information</h3>
          </div>
          <p style={{ margin: '0 0 24px 36px', color: '#64748B', fontSize: '14px' }}>Your examination details</p>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px', marginLeft: '36px' }}>
             <div style={{ background: '#F8FAFC', padding: '16px 20px', borderRadius: '8px', border: '1px solid #F1F5F9' }}>
                <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Candidate</div>
                <div style={{ fontSize: '16px', color: '#64748B', fontWeight: 700, marginTop: '6px' }}>Name unavailable</div>
                <div style={{ fontSize: '13px', color: '#2563EB', fontWeight: 600, marginTop: '2px' }}>{candidateId}</div>
             </div>
             <div style={{ background: '#F8FAFC', padding: '16px 20px', borderRadius: '8px', border: '1px solid #F1F5F9' }}>
                <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Duration</div>
                <div style={{ fontSize: '18px', color: '#0F172A', fontWeight: 700, marginTop: '6px' }}>{examConfig.totalMinutes} Minutes</div>
             </div>
             <div style={{ background: '#F8FAFC', padding: '16px 20px', borderRadius: '8px', border: '1px solid #F1F5F9' }}>
                <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Questions</div>
                <div style={{ fontSize: '18px', color: '#0F172A', fontWeight: 700, marginTop: '6px' }}>{examConfig.totalQuestions}</div>
             </div>
          </div>
        </div>

        {/* Navigation & Status Card */}
        <div className="card-shadow" style={{ background: '#FFF', borderRadius: '12px', border: '1px solid #E2E8F0', padding: '32px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '24px' }}>
             <Navigation size={24} color="#2563EB" />
             <h3 style={{ margin: 0, fontSize: '18px', color: '#0F172A', fontWeight: 700 }}>Navigation & Status</h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginLeft: '36px', marginBottom: '32px' }}>
             <div style={{ padding: '20px', border: '1px solid #E2E8F0', borderRadius: '8px', background: '#FFFFFF' }}>
                <div style={{ fontWeight: 700, color: '#0F172A', marginBottom: '8px', fontSize: '15px' }}>Save & Next</div>
                <div style={{ fontSize: '13px', color: '#64748B', lineHeight: 1.5 }}>Save your answer and move to the next question.</div>
             </div>
             <div style={{ padding: '20px', border: '1px solid #E2E8F0', borderRadius: '8px', background: '#FFFFFF' }}>
                <div style={{ fontWeight: 700, color: '#0F172A', marginBottom: '8px', fontSize: '15px' }}>Mark for Review</div>
                <div style={{ fontSize: '13px', color: '#64748B', lineHeight: 1.5 }}>Flag a question and revisit it later.</div>
             </div>
             <div style={{ padding: '20px', border: '1px solid #E2E8F0', borderRadius: '8px', background: '#FFFFFF' }}>
                <div style={{ fontWeight: 700, color: '#0F172A', marginBottom: '8px', fontSize: '15px' }}>Question Palette</div>
                <div style={{ fontSize: '13px', color: '#64748B', lineHeight: 1.5 }}>Jump directly to any question.</div>
             </div>
          </div>

          <div style={{ marginLeft: '36px', background: '#F8FAFC', padding: '24px', borderRadius: '8px', border: '1px solid #F1F5F9' }}>
            <h4 style={{ fontSize: '13px', color: '#64748B', marginBottom: '16px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Question Status Legend</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px' }}>
               <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#CBD5E1' }}></div>
                  <span style={{ fontSize: '14px', color: '#334155', fontWeight: 500 }}>Not Visited</span>
               </div>
               <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#EF4444' }}></div>
                  <span style={{ fontSize: '14px', color: '#334155', fontWeight: 500 }}>Not Answered</span>
               </div>
               <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#22C55E' }}></div>
                  <span style={{ fontSize: '14px', color: '#334155', fontWeight: 500 }}>Answered</span>
               </div>
               <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#A855F7' }}></div>
                  <span style={{ fontSize: '14px', color: '#334155', fontWeight: 500 }}>Marked for Review</span>
               </div>
               <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '18px', height: '18px', borderRadius: '50%', background: '#22C55E', position: 'relative' }}>
                     <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#A855F7', position: 'absolute', bottom: '-2px', right: '-2px' }}></div>
                  </div>
                  <span style={{ fontSize: '14px', color: '#334155', fontWeight: 500 }}>Answered & Marked</span>
               </div>
            </div>
          </div>
        </div>

        {/* Security & System Card */}
        <div className="card-shadow" style={{ background: '#F0F5FF', borderRadius: '12px', border: '1px solid #DBEAFE', padding: '32px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '4px' }}>
             <Shield size={24} color="#1D4ED8" />
             <h3 style={{ margin: 0, fontSize: '18px', color: '#1D4ED8', fontWeight: 700 }}>Secure Examination Environment</h3>
          </div>
          <p style={{ margin: '0 0 24px 36px', color: '#3B82F6', fontSize: '14px' }}>Your examination session is protected by NETI integrity monitoring.</p>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px', marginLeft: '36px' }}>
             <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', background: '#FFFFFF', padding: '20px', borderRadius: '8px', border: '1px solid #BFDBFE' }}>
                <MonitorOff size={24} color="#2563EB" style={{ flexShrink: 0 }} />
                <div>
                   <div style={{ fontWeight: 700, color: '#1E3A8A', fontSize: '14px' }}>Focus Monitoring</div>
                   <div style={{ fontSize: '13px', color: '#475569', marginTop: '6px', lineHeight: 1.4 }}>Navigating away triggers a security warning.</div>
                </div>
             </div>
             <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', background: '#FFFFFF', padding: '20px', borderRadius: '8px', border: '1px solid #BFDBFE' }}>
                <RefreshCw size={24} color="#2563EB" style={{ flexShrink: 0 }} />
                <div>
                   <div style={{ fontWeight: 700, color: '#1E3A8A', fontSize: '14px' }}>Automatic Sync</div>
                   <div style={{ fontSize: '13px', color: '#475569', marginTop: '6px', lineHeight: 1.4 }}>Answers are saved locally and synced automatically.</div>
                </div>
             </div>
             <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', background: '#FFFFFF', padding: '20px', borderRadius: '8px', border: '1px solid #BFDBFE' }}>
                <WifiOff size={24} color="#2563EB" style={{ flexShrink: 0 }} />
                <div>
                   <div style={{ fontWeight: 700, color: '#1E3A8A', fontSize: '14px' }}>Disconnect Recovery</div>
                   <div style={{ fontSize: '13px', color: '#475569', marginTop: '6px', lineHeight: 1.4 }}>Continue answering offline; data syncs when restored.</div>
                </div>
             </div>
          </div>
        </div>

        {/* Important Warning */}
        <div style={{ background: '#FFFBEB', borderRadius: '12px', border: '1px solid #FEF3C7', padding: '24px', display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
          <AlertTriangle size={24} color="#D97706" style={{ flexShrink: 0 }} />
          <div>
             <h4 style={{ margin: 0, color: '#B45309', fontSize: '15px', fontWeight: 700 }}>Before you begin</h4>
             <p style={{ margin: '4px 0 0 0', color: '#92400E', fontSize: '14px' }}>Do not refresh, close this window, or navigate away during the examination.</p>
          </div>
        </div>

      </motion.div>

      {/* Sticky Bottom Action Bar */}
      <div style={{ 
        position: 'fixed', 
        bottom: 0, 
        left: 0, 
        right: 0, 
        background: '#FFFFFF', 
        borderTop: '1px solid #E2E8F0', 
        padding: '20px 40px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        boxShadow: '0 -4px 20px rgba(0,0,0,0.05)',
        zIndex: 1000 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <input 
            type="checkbox" 
            id="ack-checkbox"
            checked={acknowledged} 
            onChange={(e) => setAcknowledged(e.target.checked)} 
            style={{ width: '22px', height: '22px', cursor: 'pointer', accentColor: '#2563EB' }}
          />
          <label htmlFor="ack-checkbox" style={{ cursor: 'pointer', fontWeight: 600, color: '#0F172A', fontSize: '15px', userSelect: 'none' }}>
            I have read and understood all examination instructions.
          </label>
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <button 
            onClick={() => navigate("/checkin")} 
            style={{ 
              padding: '0 24px', 
              height: '52px', 
              background: '#F8FAFC', 
              border: '1px solid #E2E8F0', 
              borderRadius: '8px', 
              color: '#475569', 
              fontWeight: 600, 
              fontSize: '15px', 
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
          >
            Back to Check-in
          </button>
          <button 
            onClick={() => navigate("/exam", { state })} 
            disabled={!acknowledged} 
            style={{ 
              padding: '0 32px', 
              height: '52px', 
              background: acknowledged ? '#2563EB' : '#94A3B8', 
              border: 'none', 
              borderRadius: '8px', 
              color: '#FFF', 
              fontWeight: 600, 
              fontSize: '15px', 
              cursor: acknowledged ? 'pointer' : 'not-allowed', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              transition: 'background-color 0.2s',
              boxShadow: acknowledged ? '0 4px 12px rgba(37, 99, 235, 0.2)' : 'none'
            }}
          >
            Start Examination <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </>
  );
}
