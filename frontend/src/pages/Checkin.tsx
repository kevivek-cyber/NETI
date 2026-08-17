import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/api";
import { mockData, CandidateInfo } from "../api/mock-data";
import { 
  User, 
  ShieldCheck, 
  BookOpen, 
  Calendar, 
  Building, 
  MonitorSmartphone, 
  Clock, 
  Shield, 
  ArrowRight,
  ClipboardList,
  FileText,
  MonitorOff,
  AlertTriangle,
  Loader2,
  Check
} from "lucide-react";

type CheckinState = "IDLE" | "VERIFYING" | "VERIFIED" | "ERROR";

const css = `
  .checkin-bg-mesh {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: -1;
    background-color: #F8FAFC;
    background-image: radial-gradient(#CBD5E1 1px, transparent 1px);
    background-size: 24px 24px;
    opacity: 0.4;
  }
  .checkin-bg-gradient {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: -1;
    background: radial-gradient(circle at top left, rgba(239,246,255,1) 0%, transparent 40%),
                radial-gradient(circle at bottom right, rgba(239,246,255,1) 0%, transparent 40%);
  }
  .card-shadow {
    box-shadow: 0px 4px 20px rgba(11, 35, 69, 0.04);
  }
`;

function DetailRow({ 
  icon, 
  label, 
  value, 
  valueColor = "#0F172A", 
  noBorder = false 
}: { 
  icon: React.ReactNode, 
  label: string, 
  value: string, 
  valueColor?: string, 
  noBorder?: boolean 
}) {
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'flex-start', 
      gap: '16px', 
      paddingBottom: noBorder ? 0 : '16px', 
      borderBottom: noBorder ? 'none' : '1px solid #F1F5F9' 
    }}>
      <div style={{ 
        width: '40px', 
        height: '40px', 
        borderRadius: '50%', 
        background: '#F0F5FF', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        flexShrink: 0 
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px', letterSpacing: '0.05em' }}>
          {label}
        </div>
        <div style={{ fontSize: '15px', color: valueColor, fontWeight: 700, lineHeight: '1.4', whiteSpace: 'pre-line' }}>
          {value}
        </div>
      </div>
    </div>
  );
}

export function Checkin() {
  const [candidate, setCandidate] = useState<CandidateInfo | null>(null);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [inputRollNumber, setInputRollNumber] = useState("");
  const [status, setStatus] = useState<CheckinState>("IDLE");
  const [validationError, setValidationError] = useState<string | null>(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    loadCandidateData();
  }, []);

  async function loadCandidateData() {
    setIsLoadingData(true);
    setFetchError(null);
    try {
      const data = await mockData.getCurrentCandidate();
      setCandidate(data);
      if (data.rollNumber) {
        setInputRollNumber(data.rollNumber);
      }
    } catch (err) {
      console.error("Error loading candidate data:", err);
      setFetchError("Unable to load candidate information.\nPlease check your network connection.");
    } finally {
      setIsLoadingData(false);
    }
  }

  async function handleCheckIn() {
    if (status === "VERIFYING") return;
    
    setValidationError(null);
    const trimmedInput = inputRollNumber.trim();
    
    if (!trimmedInput) {
      setValidationError("Please enter your roll number.");
      setStatus("ERROR");
      return;
    }

    if (candidate && trimmedInput !== candidate.rollNumber) {
      setValidationError("Invalid roll number. Please check and try again.");
      setStatus("ERROR");
      return;
    }

    setStatus("VERIFYING");
    
    try {
      // 1. Perform Check-in
      const checkInRes = await api.checkIn({
        candidate_id: trimmedInput,
        session_id: "2026-NEET-UG",
      });

      if (checkInRes.status !== "success") {
        throw new Error("Check-in failed on server.");
      }

      // 2. Issue Paper
      const issueRes = await api.issuePaper({
        candidate_id: trimmedInput,
        session_id: "2026-NEET-UG",
      });
      
      const session = {
        session_id: "2026-NEET-UG",
        blueprint: issueRes.paper.blueprint,
        questions: issueRes.paper.questions.length,
        marks: 720,
        bank_version: issueRes.paper.bank_version,
        blueprint_hash: "unknown",
        duration_seconds: issueRes.duration_seconds,
      };

      const paper = {
        pseudonym: issueRes.candidate_id,
        paper_hash: issueRes.paper_hash,
        paper: issueRes.paper,
        started_at: issueRes.started_at,
      };

      setStatus("VERIFIED");
      
      const { restoreSession } = await import("../hooks/useAutosave");
      const savedSession = await restoreSession(candidate!.rollNumber);
      
      let restoredState = null;
      if (savedSession && savedSession.paperHash === paper.paper_hash) {
        restoredState = savedSession;
      }
      
      setTimeout(() => {
        navigate("/instructions", { state: { paper, session, candidateId: candidate!.rollNumber, restoredState, candidate } });
      }, 800);

    } catch (e: any) {
      setValidationError(e.message || "An unexpected error occurred during check-in. Please try again.");
      console.error(e);
      setStatus("ERROR");
    }
  }

  if (fetchError) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '4rem 2rem', gap: '1rem', background: '#FFFFFF', borderRadius: '12px', border: '1px solid #DCE4EE', marginTop: '2rem' }}>
        <AlertTriangle size={48} color="#DC2626" />
        <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#0F172A' }}>Connection Lost</h3>
        <p style={{ margin: 0, color: '#64748B', textAlign: 'center', whiteSpace: 'pre-line' }}>{fetchError}</p>
        <button 
          onClick={loadCandidateData}
          style={{ padding: '0.75rem 2rem', background: '#2563EB', color: '#FFF', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', marginTop: '1rem' }}>
          Retry
        </button>
      </div>
    );
  }

  const isVerifying = status === "VERIFYING";

  return (
    <>
      <style>{css}</style>
      <div className="checkin-bg-gradient" />
      <div className="checkin-bg-mesh" />

      <div style={{ maxWidth: '1024px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px', fontFamily: '"Inter", sans-serif' }}>
        
        {/* Title Area */}
        <div style={{ textAlign: 'center', marginBottom: '16px', paddingTop: '16px' }}>
          <h2 style={{ fontSize: '36px', color: '#0F172A', margin: '0', fontWeight: 700, letterSpacing: '-0.02em' }}>
            Candidate <span style={{ color: '#2563EB' }}>Check-in</span>
          </h2>
          <p style={{ color: '#64748B', fontSize: '15px', margin: '12px 0 16px 0', fontWeight: 500 }}>
            Verify your identity and examination details before proceeding.
          </p>
          <div style={{ width: '48px', height: '4px', backgroundColor: '#2563EB', borderRadius: '2px', margin: '0 auto' }}></div>
        </div>

        {/* 1. Candidate Verification Card */}
        <div className="card-shadow" style={{ background: '#FFFFFF', borderRadius: '12px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
          {/* Card Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 32px', height: '80px', borderBottom: '1px solid #E2E8F0', background: '#FFFFFF' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '44px', height: '44px', backgroundColor: '#F0F5FF', border: '1px solid #DBEAFE', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <User size={22} color="#2563EB" />
              </div>
              <div>
                <h3 style={{ margin: 0, color: '#0F172A', fontSize: '16px', fontWeight: 700 }}>Candidate Verification</h3>
                <p style={{ margin: '2px 0 0 0', color: '#64748B', fontSize: '13px' }}>Please verify all the details carefully. These details are as per our records.</p>
              </div>
            </div>
            <div>
              <ShieldCheck size={56} color="#F8FAFC" />
            </div>
          </div>

          <div style={{ padding: '32px' }} className={isLoadingData ? "skeleton-pulse" : ""}>
            {isLoadingData ? (
              <div style={{ display: 'flex', gap: '48px' }}>
                 <div style={{ width: '280px', height: '320px', backgroundColor: '#E2E8F0', borderRadius: '12px' }}></div>
                 <div style={{ flex: 1, display: 'flex', gap: '32px' }}>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      <div style={{ height: '60px', backgroundColor: '#E2E8F0', borderRadius: '4px' }}></div>
                      <div style={{ height: '60px', backgroundColor: '#E2E8F0', borderRadius: '4px' }}></div>
                      <div style={{ height: '60px', backgroundColor: '#E2E8F0', borderRadius: '4px' }}></div>
                    </div>
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      <div style={{ height: '60px', backgroundColor: '#E2E8F0', borderRadius: '4px' }}></div>
                      <div style={{ height: '60px', backgroundColor: '#E2E8F0', borderRadius: '4px' }}></div>
                      <div style={{ height: '60px', backgroundColor: '#E2E8F0', borderRadius: '4px' }}></div>
                    </div>
                 </div>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '48px', flexWrap: 'wrap' }}>
                
                {/* Left Column: Photo */}
                <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ 
                    width: '100%', 
                    aspectRatio: '1/1', 
                    border: '1px solid #E2E8F0', 
                    borderRadius: '12px', 
                    backgroundColor: '#F8FAFC', 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    overflow: 'hidden',
                    padding: '8px'
                  }}>
                    {candidate?.photoUrl ? (
                      <img src={candidate.photoUrl} alt="Candidate" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '8px', display: 'block' }} />
                    ) : (
                      <User size={80} color="#94A3B8" />
                    )}
                  </div>
                  <div style={{ backgroundColor: '#F0F5FF', height: '64px', borderRadius: '8px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                      <ShieldCheck size={16} color="#2563EB" />
                      <span style={{ color: '#2563EB', fontWeight: 600, fontSize: '14px' }}>Identity Verified</span>
                    </div>
                    <span style={{ color: '#64748B', fontSize: '12px' }}>Photo captured at center</span>
                  </div>
                </div>

                {/* Right Column: Information Rows */}
                <div style={{ flex: 1, display: 'flex', gap: '32px', minWidth: '400px' }}>
                  
                  {/* Info Col 1 */}
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <DetailRow 
                      icon={<User size={18} color="#3B82F6" />} 
                      label="Candidate Name" 
                      value={candidate?.name || "Not available"} 
                    />
                    <DetailRow 
                      icon={<FileText size={18} color="#3B82F6" />} 
                      label="Roll Number" 
                      value={candidate?.rollNumber || "Not available"} 
                    />
                    <DetailRow 
                      icon={<BookOpen size={18} color="#3B82F6" />} 
                      label="Examination" 
                      value={candidate?.examName || "Not available"} 
                    />
                    <DetailRow 
                      icon={<Calendar size={18} color="#3B82F6" />} 
                      label="Date & Time" 
                      value={candidate?.examDate || "Not available"} 
                      noBorder
                    />
                  </div>

                  {/* Info Col 2 */}
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <DetailRow 
                      icon={<Building size={18} color="#3B82F6" />} 
                      label="Exam Center" 
                      value={candidate?.examCenter || "Not available"} 
                    />
                    <DetailRow 
                      icon={<MonitorSmartphone size={18} color="#3B82F6" />} 
                      label="Seat Number" 
                      value={candidate?.seatNumber || "Not available"} 
                      valueColor="#2563EB"
                    />
                    <DetailRow 
                      icon={<Clock size={18} color="#3B82F6" />} 
                      label="Duration" 
                      value={candidate?.examDuration || "Not available"} 
                      noBorder
                    />
                  </div>

                </div>
              </div>
            )}
          </div>
        </div>

        {/* 2. Confirm Roll Number Card */}
        <div className="card-shadow" style={{ background: '#FFFFFF', borderRadius: '12px', border: '1px solid #E2E8F0', padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '24px' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', backgroundColor: '#F0F5FF', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Shield size={24} color="#2563EB" />
            </div>
            <div>
              <h3 style={{ margin: 0, color: '#0F172A', fontSize: '16px', fontWeight: 700 }}>Confirm Roll Number</h3>
              <p style={{ margin: '4px 0 0 0', color: '#64748B', fontSize: '13px' }}>Enter your roll number to verify and continue.</p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <input 
                type="text"
                value={inputRollNumber} 
                onChange={(e) => {
                  setInputRollNumber(e.target.value);
                  if (status === "ERROR") setStatus("IDLE");
                  if (validationError) setValidationError(null);
                }} 
                disabled={isVerifying || isLoadingData || status === "VERIFIED"}
                placeholder="Enter your roll number"
                style={{ 
                  width: '280px', 
                  height: '48px',
                  padding: '0 16px', 
                  border: validationError ? '1px solid #DC2626' : '1px solid #E2E8F0', 
                  borderRadius: '8px',
                  fontSize: '15px',
                  color: '#0F172A',
                  outline: 'none',
                }}
              />
              {validationError && (
                <span style={{ color: '#DC2626', fontSize: '12px', fontWeight: 500, position: 'absolute', marginTop: '52px' }}>
                  {validationError}
                </span>
              )}
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
              {status === "VERIFIED" && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#16A34A', fontSize: '12px', fontWeight: 600, position: 'absolute', marginTop: '-24px' }}>
                  <Check size={14} /> Roll number verified
                </div>
              )}
              <button 
                onClick={handleCheckIn} 
                disabled={isVerifying || isLoadingData || status === "VERIFIED"}
                style={{ 
                  height: '48px',
                  width: '240px',
                  backgroundColor: isVerifying || isLoadingData ? '#94A3B8' : status === "VERIFIED" ? '#16A34A' : '#1D4ED8',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '15px',
                  cursor: isVerifying || isLoadingData || status === "VERIFIED" ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'background-color 0.2s',
                }}
              >
                {status === "VERIFYING" ? (
                  <>
                    <Loader2 size={18} className="spin" /> Verifying...
                  </>
                ) : status === "VERIFIED" ? (
                  <>
                    Verified <Check size={18} />
                  </>
                ) : (
                  <>
                    Check In & Continue <ArrowRight size={18} />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 3. Examination Overview Card */}
        <div className="card-shadow" style={{ background: '#FFFFFF', borderRadius: '12px', border: '1px solid #E2E8F0', padding: '24px 32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
            <ClipboardList size={22} color="#2563EB" />
            <h3 style={{ margin: 0, color: '#0F172A', fontSize: '16px', fontWeight: 700 }}>Examination Overview</h3>
          </div>

          {isLoadingData ? (
             <div className="skeleton-pulse" style={{ height: '80px', borderRadius: '8px' }}></div>
          ) : (
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              
              <div style={{ flex: 1, minWidth: '140px', backgroundColor: '#F0F5FF', borderRadius: '8px', padding: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ width: '48px', height: '48px', backgroundColor: '#FFFFFF', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <FileText size={24} color="#2563EB" />
                </div>
                <div>
                  <div style={{ fontSize: '24px', color: '#0F172A', fontWeight: 700, lineHeight: 1.1 }}>{candidate?.totalQuestions || 0}</div>
                  <div style={{ fontSize: '12px', color: '#475569', fontWeight: 600, marginTop: '2px' }}>Total Questions</div>
                </div>
              </div>

              <div style={{ flex: 1, minWidth: '140px', backgroundColor: '#F3E8FF', borderRadius: '8px', padding: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ width: '48px', height: '48px', backgroundColor: '#FFFFFF', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Clock size={24} color="#9333EA" />
                </div>
                <div>
                  <div style={{ fontSize: '24px', color: '#0F172A', fontWeight: 700, lineHeight: 1.1 }}>{candidate?.examDuration ? parseInt(candidate.examDuration) * 60 : 0}</div>
                  <div style={{ fontSize: '12px', color: '#475569', fontWeight: 600, marginTop: '2px' }}>Total Minutes</div>
                </div>
              </div>

              {candidate?.subjects?.map((subj, idx) => {
                const colors = [
                  { bg: '#DCFCE7', iconBg: '#FFFFFF', text: '#16A34A', label: '#16A34A' }, // Physics
                  { bg: '#FFEDD5', iconBg: '#FFFFFF', text: '#EA580C', label: '#EA580C' }, // Chemistry
                  { bg: '#CCFBF1', iconBg: '#FFFFFF', text: '#0D9488', label: '#0D9488' }  // Biology
                ];
                const c = colors[idx % colors.length];
                
                return (
                  <div key={subj.name} style={{ flex: 1, minWidth: '140px', backgroundColor: c.bg, borderRadius: '8px', padding: '16px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ width: '48px', height: '48px', backgroundColor: c.iconBg, borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <BookOpen size={24} color={c.text} />
                    </div>
                    <div>
                      <div style={{ fontSize: '24px', color: '#0F172A', fontWeight: 700, lineHeight: 1.1 }}>{subj.count}</div>
                      <div style={{ fontSize: '12px', color: c.label, fontWeight: 600, marginTop: '2px' }}>{subj.name}</div>
                    </div>
                  </div>
                );
              })}

            </div>
          )}
        </div>

        {/* 4. Footer Warnings */}
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          
          <div style={{ flex: 1, minWidth: '300px', background: '#F0F5FF', borderRadius: '12px', padding: '20px 24px', display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div style={{ width: '48px', height: '48px', backgroundColor: '#FFFFFF', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid #DBEAFE' }}>
              <Shield size={24} color="#1D4ED8" />
            </div>
            <div>
              <h4 style={{ margin: '0 0 2px 0', color: '#1D4ED8', fontSize: '14px', fontWeight: 700 }}>Secure Examination Environment</h4>
              <p style={{ margin: 0, color: '#475569', fontSize: '12px', lineHeight: 1.5 }}>Your session is protected and examination activity may be monitored for integrity and security purposes.</p>
            </div>
          </div>

          <div style={{ flex: 1, minWidth: '300px', background: '#F8FAFC', borderRadius: '12px', padding: '20px 24px', display: 'flex', gap: '16px', alignItems: 'center', border: '1px solid #E2E8F0' }}>
            <div style={{ width: '48px', height: '48px', backgroundColor: '#FFFFFF', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, border: '1px solid #E2E8F0' }}>
              <MonitorOff size={24} color="#64748B" />
            </div>
            <div>
              <h4 style={{ margin: '0 0 2px 0', color: '#0F172A', fontSize: '14px', fontWeight: 700 }}>Important</h4>
              <p style={{ margin: 0, color: '#475569', fontSize: '12px', lineHeight: 1.5 }}>Do not refresh, close or navigate away from this page until the check-in process is complete.</p>
            </div>
          </div>

        </div>

      </div>
    </>
  );
}
