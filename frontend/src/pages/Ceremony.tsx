import { useState } from "react";
import { api } from "../api/api";
import { Lock, Unlock, ShieldAlert, Key, Loader2, CheckCircle2 } from "lucide-react";

type CeremonyState = "LOCKED" | "UNLOCKING" | "UNLOCKED" | "ERROR";

export function Ceremony() {
  const [status, setStatus] = useState<CeremonyState>("LOCKED");
  const [sharesInput, setSharesInput] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleUnlock = async () => {
    setStatus("UNLOCKING");
    setErrorMsg("");

    try {
      // Parse input lines like "1: 0123abc...", "2: 456def..."
      const lines = sharesInput.split("\n").filter(l => l.trim().length > 0);
      const shares = lines.map(line => {
        const parts = line.split(":");
        if (parts.length !== 2) throw new Error("Invalid share format. Expected 'index: hex_string'");
        return {
          index: parseInt(parts[0].trim(), 10),
          share_hex: parts[1].trim()
        };
      });

      if (shares.length < 2) {
        throw new Error("At least 2 shares are required to unlock the bank.");
      }

      await api.ceremonyUnlock({
        session_id: "2026-NEET-UG",
        shares
      });

      setStatus("UNLOCKED");
    } catch (e: any) {
      console.error(e);
      setErrorMsg(e.message || "Failed to unlock the exam bank.");
      setStatus("ERROR");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: '#F8FAFC', padding: '24px', fontFamily: '"Inter", sans-serif' }}>
      
      <div style={{ maxWidth: '600px', width: '100%', background: '#FFFFFF', borderRadius: '12px', padding: '40px', boxShadow: '0 4px 20px rgba(15, 23, 42, 0.05)', border: '1px solid #E2E8F0' }}>
        
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
          {status === "LOCKED" || status === "ERROR" ? (
            <div style={{ width: '64px', height: '64px', backgroundColor: '#FEE2E2', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Lock size={32} color="#DC2626" />
            </div>
          ) : status === "UNLOCKING" ? (
            <div style={{ width: '64px', height: '64px', backgroundColor: '#DBEAFE', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Loader2 size={32} color="#2563EB" className="spin" />
            </div>
          ) : (
            <div style={{ width: '64px', height: '64px', backgroundColor: '#DCFCE7', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Unlock size={32} color="#16A34A" />
            </div>
          )}
        </div>

        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{ fontSize: '24px', color: '#0F172A', fontWeight: 700, margin: '0 0 8px 0' }}>Custodian Key Ceremony</h1>
          <p style={{ color: '#64748B', fontSize: '15px', margin: 0 }}>
            {status === "UNLOCKED" 
              ? "The exam bank has been successfully decrypted and the master seed is loaded in memory."
              : "Enter cryptographic shares to decrypt the exam bank and authorise the session."}
          </p>
        </div>

        {status !== "UNLOCKED" && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '14px', fontWeight: 600, color: '#1E293B' }}>Cryptographic Shares</label>
              <textarea 
                value={sharesInput}
                onChange={(e) => {
                  setSharesInput(e.target.value);
                  if (status === "ERROR") setStatus("LOCKED");
                }}
                disabled={status === "UNLOCKING"}
                placeholder="Format:&#10;1: <share_hex>&#10;2: <share_hex>"
                style={{ width: '100%', height: '160px', padding: '16px', borderRadius: '8px', border: '1px solid #CBD5E1', fontSize: '14px', fontFamily: 'monospace', resize: 'none', outline: 'none' }}
              />
            </div>

            {status === "ERROR" && (
              <div style={{ padding: '12px', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: '8px', display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <ShieldAlert size={20} color="#DC2626" style={{ flexShrink: 0, marginTop: '2px' }} />
                <span style={{ fontSize: '14px', color: '#991B1B', fontWeight: 500 }}>{errorMsg}</span>
              </div>
            )}

            <button 
              onClick={handleUnlock}
              disabled={status === "UNLOCKING" || sharesInput.trim().length === 0}
              style={{
                marginTop: '8px',
                height: '48px',
                background: status === "UNLOCKING" ? '#94A3B8' : '#2563EB',
                color: '#FFFFFF',
                borderRadius: '8px',
                border: 'none',
                fontWeight: 600,
                fontSize: '15px',
                cursor: status === "UNLOCKING" || sharesInput.trim().length === 0 ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'background-color 0.2s'
              }}
            >
              {status === "UNLOCKING" ? (
                <> <Loader2 size={18} className="spin" /> Unlocking Bank... </>
              ) : (
                <> <Key size={18} /> Authorise Session </>
              )}
            </button>
          </div>
        )}

        {status === "UNLOCKED" && (
          <div style={{ padding: '24px', background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '8px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <CheckCircle2 size={48} color="#16A34A" />
            <div style={{ textAlign: 'center' }}>
              <h3 style={{ margin: '0 0 8px 0', color: '#166534', fontSize: '16px', fontWeight: 700 }}>Bank Unlocked</h3>
              <p style={{ margin: 0, color: '#15803D', fontSize: '14px', lineHeight: 1.5 }}>
                The exam bank is decrypted. The master seed has been established. Candidates can now check-in and receive their deterministic papers.
              </p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
