import { useExamTimer } from "../../hooks/useExamTimer";
import { ConnectionStatus } from "../../hooks/useConnectionStatus";
import { SaveStatus } from "../../hooks/useAutosave";
import clsx from "clsx";
import { Wifi, CloudOff, CheckCircle, Loader2, AlertCircle, User, Building, MonitorSmartphone } from "lucide-react";

interface ExamHeaderProps {
  examName?: string;
  candidateId: string;
  candidateName?: string;
  connectionStatus: ConnectionStatus;
  saveStatus: SaveStatus;
  timer: ReturnType<typeof useExamTimer>;
}

export function ExamHeader({
  examName = "NETI Examination",
  candidateId,
  candidateName = "Aarav Sharma",
  connectionStatus,
  saveStatus,
  timer,
}: ExamHeaderProps) {
  let timerClass = "timer-normal";
  if (timer.isWarning) timerClass = "timer-warning";
  if (timer.isDanger) timerClass = "timer-danger";
  if (timer.isCritical) timerClass = "timer-critical pulse";

  return (
    <header className="cbt-header">
      
      {/* BRANDING */}
      <div className="header-brand-block">
        <img 
          src="/logo.png" 
          alt="NETI Logo" 
          style={{ width: '40px', height: '40px', objectFit: 'contain', borderRadius: '4px' }} 
        />
        <div className="brand-text">
          <h1 className="brand-title">NETI</h1>
          <span className="brand-subtitle">Non-Exploitable Test Integrity</span>
        </div>
      </div>

      {/* EXAM NAME */}
      <div className="header-info-block border-left">
        <h2 className="exam-title">{examName}</h2>
        <span className="tag-mock">Mock Test</span>
      </div>

      {/* CANDIDATE INFO */}
      <div className="header-info-block border-left">
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div className="icon-circle"><User size={18} /></div>
          <div>
            <div className="info-label">Candidate</div>
            <div className="info-value-bold">{candidateName}</div>
            <div className="info-sub">{candidateId}</div>
          </div>
        </div>
      </div>

      {/* CENTER INFO */}
      <div className="header-info-block border-left">
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div className="icon-circle"><Building size={18} /></div>
          <div>
            <div className="info-label">Exam Center</div>
            <div className="info-value-bold">TCS iON Digital Zone</div>
            <div className="info-sub">Mumbai</div>
          </div>
        </div>
      </div>

      {/* SEAT NO */}
      <div className="header-info-block border-left">
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div className="icon-circle"><MonitorSmartphone size={18} /></div>
          <div>
            <div className="info-label">Seat No.</div>
            <div className="info-value-bold" style={{ fontSize: '1.25rem' }}>A-42</div>
          </div>
        </div>
      </div>

      {/* STATUS BLOCK */}
      <div className="header-status-block border-left">
        <div className="status-row">
          <span className="autosave-status" aria-live="polite">
            {saveStatus === "Saved" && <><CheckCircle size={14} className="text-success" /> <span className="status-text text-success">Saved</span></>}
            {saveStatus === "Saving..." && <><Loader2 size={14} className="pulse" /> <span className="status-text">Saving...</span></>}
            {saveStatus === "Offline Saved" && <><CheckCircle size={14} className="text-success" /> <span className="status-text text-success">Offline Saved</span></>}
            {saveStatus === "Sync Pending" && <><Loader2 size={14} /> <span className="status-text">Sync Pending</span></>}
            {saveStatus === "Error" && <><AlertCircle size={14} className="text-danger" /> <span className="status-text text-danger">Error</span></>}
          </span>
          <span className="status-time">just now</span>
        </div>
        <div className="status-row">
          <span className={clsx("connection-status", `status-${connectionStatus.toLowerCase()}`)} aria-live="polite">
            {connectionStatus === "Connected" ? <Wifi size={14} color="var(--success)" /> : <CloudOff size={14} color="var(--danger)" />}
            {connectionStatus === "Connected" && <span className="status-text text-success">Connected</span>}
            {connectionStatus === "Reconnecting" && <span className="status-text">Reconnecting</span>}
            {connectionStatus === "Offline" && <span className="status-text text-danger">Offline</span>}
          </span>
        </div>
      </div>

      {/* TIMER */}
      <div className="header-timer-block border-left">
        <div 
          className={clsx("status-item timer", timerClass)}
          aria-live="polite" 
          aria-atomic="true" 
          aria-label={`Time Remaining: ${timer.formattedTime}`}
        >
          <span className="timer-label" aria-hidden="true">TIME REMAINING</span>
          <span className="timer-value mono" aria-hidden="true">{timer.formattedTime}</span>
          <div className="timer-units"><span>Hr</span><span>Min</span><span>Sec</span></div>
        </div>
      </div>

    </header>
  );
}
