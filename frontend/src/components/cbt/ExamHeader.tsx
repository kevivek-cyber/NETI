import { useExamTimer } from "../../hooks/useExamTimer";
import { ConnectionStatus } from "../../hooks/useConnectionStatus";
import { SaveStatus } from "../../hooks/useAutosave";
import { CloudOff, CheckCircle, Loader2, AlertCircle, Clock, ShieldCheck, User, MonitorSmartphone } from "lucide-react";

interface ExamHeaderProps {
  examName?: string;
  candidateId: string;
  candidateName?: string;
  connectionStatus: ConnectionStatus;
  saveStatus: SaveStatus;
  timer: ReturnType<typeof useExamTimer>;
  onSubmit: () => void;
}

export function ExamHeader({
  examName = "National Eligibility cum Entrance Test (NEET)",
  candidateId,
  candidateName = "Aarav Sharma",
  connectionStatus,
  saveStatus,
  timer,
  onSubmit,
}: ExamHeaderProps) {
  const isDanger = timer.isDanger || timer.isCritical;
  
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: '72px',
      padding: '0 24px',
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid #D9E2EF',
      boxShadow: '0 2px 8px rgba(23, 42, 70, 0.04)',
      fontFamily: '"Inter", sans-serif'
    }}>
      
      {/* LEFT: Branding */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <img src="/logo.png" alt="NETI Logo" style={{ width: '40px', height: '40px', objectFit: 'contain' }} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <h1 style={{ margin: 0, fontSize: '20px', color: '#172A46', fontWeight: 800, lineHeight: 1.1 }}>NETI</h1>
            <span style={{ fontSize: '10px', color: '#64748B', fontWeight: 700, letterSpacing: '0.05em' }}>
              NON-EXPLOITABLE<br/>TEST INTEGRITY
            </span>
          </div>
        </div>
        
        <div style={{ paddingLeft: '24px', borderLeft: '1px solid #D9E2EF', height: '40px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
           <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>Examination</span>
           <span style={{ fontSize: '14px', color: '#172A46', fontWeight: 700 }}>{examName}</span>
        </div>
      </div>

      {/* CENTER: Candidate & Seat Info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
         <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#F5F8FC', padding: '8px 16px', borderRadius: '8px', border: '1px solid #D9E2EF' }}>
            <User size={16} color="#2563EB" />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
               <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, lineHeight: 1 }}>{candidateId}</span>
               <span style={{ fontSize: '13px', color: '#172A46', fontWeight: 700, marginTop: '2px' }}>{candidateName}</span>
            </div>
         </div>
         <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#F5F8FC', padding: '8px 16px', borderRadius: '8px', border: '1px solid #D9E2EF' }}>
            <MonitorSmartphone size={16} color="#2563EB" />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
               <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, lineHeight: 1 }}>Seat No.</span>
               <span style={{ fontSize: '13px', color: '#172A46', fontWeight: 700, marginTop: '2px' }}>A-42</span>
            </div>
         </div>
      </div>

      {/* RIGHT: Status & Timer */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
         
         <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
               {saveStatus === "Saved" && <><CheckCircle size={12} color="#16A34A" /> <span style={{ fontSize: '11px', fontWeight: 600, color: '#16A34A' }}>Saved just now</span></>}
               {saveStatus === "Saving..." && <><Loader2 size={12} color="#64748B" className="pulse" /> <span style={{ fontSize: '11px', fontWeight: 600, color: '#64748B' }}>Saving...</span></>}
               {saveStatus === "Offline Saved" && <><CheckCircle size={12} color="#16A34A" /> <span style={{ fontSize: '11px', fontWeight: 600, color: '#16A34A' }}>Offline Saved</span></>}
               {saveStatus === "Sync Pending" && <><Loader2 size={12} color="#F59E0B" /> <span style={{ fontSize: '11px', fontWeight: 600, color: '#F59E0B' }}>Syncing</span></>}
               {saveStatus === "Error" && <><AlertCircle size={12} color="#EF4444" /> <span style={{ fontSize: '11px', fontWeight: 600, color: '#EF4444' }}>Save Error</span></>}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
               {connectionStatus === "Connected" ? <ShieldCheck size={12} color="#16A34A" /> : <CloudOff size={12} color="#EF4444" />}
               <span style={{ fontSize: '11px', fontWeight: 600, color: connectionStatus === "Connected" ? '#16A34A' : '#EF4444' }}>
                 {connectionStatus === "Connected" ? "Secure Connection" : "Connection Lost"}
               </span>
            </div>
         </div>

         <div style={{ height: '32px', width: '1px', backgroundColor: '#D9E2EF' }}></div>

         <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px', 
            background: isDanger ? '#FEF2F2' : '#EFF6FF', 
            padding: '8px 16px', 
            borderRadius: '8px', 
            border: `1px solid ${isDanger ? '#FCA5A5' : '#BFDBFE'}` 
         }}>
            <Clock size={20} color={isDanger ? '#EF4444' : '#2563EB'} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
               <span style={{ fontSize: '10px', color: isDanger ? '#DC2626' : '#2563EB', fontWeight: 700, letterSpacing: '0.05em' }}>TIME LEFT</span>
               <span style={{ fontSize: '20px', color: isDanger ? '#DC2626' : '#172A46', fontWeight: 800, lineHeight: 1, fontFamily: 'monospace' }}>
                  {timer.formattedTime}
               </span>
            </div>
         </div>

         <button 
           onClick={onSubmit}
           className={isDanger ? "pulse" : ""}
           style={{
             background: '#DC2626',
             color: '#FFFFFF',
             border: 'none',
             borderRadius: '8px',
             padding: '8px 24px',
             fontWeight: 700,
             fontSize: '15px',
             cursor: 'pointer',
             height: '42px',
             boxShadow: isDanger ? '0 0 12px rgba(220, 38, 38, 0.6)' : 'none',
             transition: 'all 0.2s',
             display: 'flex',
             alignItems: 'center',
             justifyContent: 'center'
           }}
         >
           Submit
         </button>
      </div>

    </header>
  );
}
