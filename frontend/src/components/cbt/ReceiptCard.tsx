import { useState } from "react";
import type { ReceiptPayload } from "../../api/api";
import { CheckCircle, ShieldCheck, Download, Copy, Check, ChevronDown, ChevronUp, Lock } from "lucide-react";
import jsPDF from "jspdf";

function CopyableField({ label, value, isMonospace = false }: { label: string; value: string; isMonospace?: boolean }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
        {label}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '6px', padding: '10px 12px', gap: '12px' }}>
        <div style={{ 
          wordBreak: 'break-all',
          fontFamily: isMonospace ? 'ui-monospace, "Cascadia Code", Consolas, monospace' : 'inherit', 
          fontSize: '13px', 
          color: '#0F172A',
          lineHeight: '1.4'
        }}>
          {value}
        </div>
        <button 
          onClick={handleCopy} 
          title="Copy to clipboard"
          aria-label={`Copy ${label}`}
          style={{ 
            background: copied ? '#DCFCE7' : '#FFFFFF', 
            border: `1px solid ${copied ? '#BBF7D0' : '#CBD5E1'}`, 
            borderRadius: '6px', 
            padding: '6px 12px', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            fontSize: '12px', 
            fontWeight: 600, 
            color: copied ? '#16A34A' : '#475569', 
            cursor: 'pointer', 
            transition: 'all 0.2s ease',
            flexShrink: 0
          }}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
    </div>
  );
}

export function ReceiptCard({ receipt, paperHash }: { receipt: ReceiptPayload; paperHash: string }) {
  const [isProofExpanded, setIsProofExpanded] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleDownloadPDF = async () => {
    setIsGenerating(true);
    try {
      // Slight delay to allow UI to render the "Generating" state
      await new Promise(r => setTimeout(r, 50));

      const doc = new jsPDF();
      const margin = 20;
      const maxWidth = 170; // A4 width is 210, minus 20 margin on both sides
      
      // Title & Branding
      doc.setFontSize(22);
      doc.setTextColor(30, 58, 138); // #1E3A8A primary
      doc.text("NETI", margin, 30);
      
      doc.setFontSize(14);
      doc.setTextColor(15, 23, 42); // #0F172A
      doc.text("NON-EXPLOITABLE TEST INTEGRITY", margin, 40);
      
      doc.setFontSize(12);
      doc.setTextColor(100, 116, 139); // muted
      doc.text("National Eligibility cum Entrance Test (NEET)", margin, 48);
      
      // Status
      doc.setFontSize(16);
      doc.setTextColor(22, 163, 74); // success
      doc.text("Examination Submitted Successfully", margin, 65);
      
      // Cryptographic Proof Details
      doc.setFontSize(11);
      doc.setTextColor(15, 23, 42);
      
      doc.setFont("helvetica", "bold");
      doc.text("Receipt ID / Index:", margin, 85);
      doc.setFont("helvetica", "normal");
      doc.text(`#${receipt.inclusion_proof.index}`, margin, 92);
      
      doc.setFont("helvetica", "bold");
      doc.text("Session ID:", margin, 102);
      doc.setFont("helvetica", "normal");
      doc.text(receipt.session_id || "2026-NEET-UG", margin, 109);
      
      doc.setFont("helvetica", "bold");
      doc.text("Paper Hash:", margin, 119);
      doc.setFont("courier", "normal");
      doc.setFontSize(10);
      const paperHashLines = doc.splitTextToSize(paperHash, maxWidth);
      doc.text(paperHashLines, margin, 126);
      const paperHashHeight = paperHashLines.length * 5;
      
      const rootYLabel = 126 + paperHashHeight + 5;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.text("Ledger Root:", margin, rootYLabel);
      doc.setFont("courier", "normal");
      doc.setFontSize(10);
      const rootLines = doc.splitTextToSize(receipt.merkle_root, maxWidth);
      doc.text(rootLines, margin, rootYLabel + 7);
      const rootHeight = rootLines.length * 5;
      
      const statusYLabel = rootYLabel + 7 + rootHeight + 5;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.text("Verification Status:", margin, statusYLabel);
      doc.setFont("helvetica", "normal");
      doc.setTextColor(22, 163, 74); // success color
      doc.text("Verified", margin, statusYLabel + 7);
      doc.setTextColor(15, 23, 42);
      
      // Merkle Proof
      let y = statusYLabel + 22;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text(`Merkle Inclusion Proof (${receipt.inclusion_proof.path.length} steps)`, margin, y);
      
      y += 10;
      doc.setFontSize(9);
      doc.setFont("courier", "normal");
      
      receipt.inclusion_proof.path.forEach((step: any) => {
        const stepText = `[${step.side}] ${step.hash}`;
        const stepLines = doc.splitTextToSize(stepText, maxWidth);
        const stepHeight = stepLines.length * 4.5;
        
        if (y + stepHeight > 280) {
          doc.addPage();
          y = 20;
        }
        doc.text(stepLines, margin, y);
        y += stepHeight + 2;
      });
      
      doc.save(`NETI_Submission_Receipt_${receipt.inclusion_proof.index}.pdf`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ padding: '40px 24px', background: '#F1F5F9', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', fontFamily: '"Inter", sans-serif' }}>
      
      {/* BRANDING HEADER */}
      <div style={{ maxWidth: '800px', width: '100%', display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '32px' }}>
        <ShieldCheck size={36} color="#1E3A8A" style={{ marginTop: '2px' }} />
        <div>
          <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 800, color: '#1E3A8A', letterSpacing: '0.02em', lineHeight: 1.1 }}>NETI</h1>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#475569', marginTop: '4px' }}>NON-EXPLOITABLE TEST INTEGRITY</div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>National Eligibility cum Entrance Test (NEET)</div>
        </div>
      </div>

      <div style={{ maxWidth: '800px', width: '100%', background: '#FFFFFF', borderRadius: '12px', boxShadow: '0 4px 24px rgba(15, 23, 42, 0.06)', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        
        {/* SUCCESS HEADER */}
        <div style={{ padding: '48px 32px', textAlign: 'center', borderBottom: '1px solid #E2E8F0', background: '#FFFFFF' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '72px', height: '72px', background: '#DCFCE7', borderRadius: '50%', color: '#16A34A', marginBottom: '24px', animation: 'scaleIn 0.3s ease-out' }}>
            <CheckCircle size={36} strokeWidth={2.5} />
          </div>
          <h2 style={{ fontSize: '28px', fontWeight: 800, color: '#0F172A', margin: '0 0 12px 0', letterSpacing: '-0.02em' }}>Examination Submitted Successfully</h2>
          <p style={{ margin: 0, color: '#475569', fontSize: '16px', lineHeight: 1.5 }}>
            Your responses have been securely recorded and anchored to the tamper-evident ledger.
          </p>
        </div>

        {/* RECEIPT CONTENT */}
        <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          {/* TOP BAR: Verified + Receipt Info */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '8px', padding: '24px', display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
              <ShieldCheck size={32} color="#16A34A" style={{ marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '18px', fontWeight: 800, color: '#166534', marginBottom: '6px', letterSpacing: '0.02em' }}>VERIFIED</div>
                <div style={{ fontSize: '14px', color: '#15803D', fontWeight: 500 }}>Cryptographic receipt validated</div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '16px', background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Receipt ID</span>
                <span style={{ fontSize: '16px', fontWeight: 800, color: '#0F172A' }}>#{receipt.inclusion_proof.index}</span>
              </div>
              <div style={{ borderBottom: '1px solid #E2E8F0' }}></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Session ID</span>
                <span style={{ fontSize: '15px', fontWeight: 600, color: '#334155' }}>{receipt.session_id || "2026-NEET-UG"}</span>
              </div>
            </div>
          </div>

          {/* CRYPTO HASHS */}
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0F172A', textTransform: 'uppercase', marginBottom: '20px', letterSpacing: '0.05em', borderBottom: '2px solid #E2E8F0', paddingBottom: '12px' }}>
              Cryptographic Artifacts
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <CopyableField label="Paper Hash" value={paperHash} isMonospace={true} />
              <CopyableField label="Ledger Root" value={receipt.merkle_root} isMonospace={true} />
            </div>
          </div>

          {/* MERKLE PROOF */}
          <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', overflow: 'hidden' }}>
            <button 
              onClick={() => setIsProofExpanded(!isProofExpanded)}
              aria-expanded={isProofExpanded}
              style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', background: isProofExpanded ? '#F1F5F9' : '#F8FAFC', border: 'none', cursor: 'pointer', outline: 'none', transition: 'background 0.2s' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '15px', fontWeight: 700, color: '#1E293B' }}>Merkle Inclusion Proof</span>
                <span style={{ fontSize: '12px', background: '#E2E8F0', color: '#475569', padding: '4px 10px', borderRadius: '12px', fontWeight: 700 }}>
                  {receipt.inclusion_proof.path.length} {receipt.inclusion_proof.path.length === 1 ? 'step' : 'steps'}
                </span>
              </div>
              {isProofExpanded ? <ChevronUp size={20} color="#64748B" /> : <ChevronDown size={20} color="#64748B" />}
            </button>
            
            {isProofExpanded && (
              <div style={{ padding: '24px', background: '#FFFFFF', borderTop: '1px solid #E2E8F0' }}>
                {receipt.inclusion_proof.path.length === 0 ? (
                  <div style={{ fontSize: '14px', color: '#64748B', textAlign: 'center', padding: '20px 0', fontWeight: 500 }}>
                    No Merkle inclusion steps were returned for this receipt.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {receipt.inclusion_proof.path.map((step: any, i: number) => (
                      <div key={i} style={{ borderBottom: i !== receipt.inclusion_proof.path.length - 1 ? '1px solid #F1F5F9' : 'none', paddingBottom: i !== receipt.inclusion_proof.path.length - 1 ? '20px' : '0' }}>
                        <div style={{ fontSize: '13px', fontWeight: 700, color: '#0F172A', marginBottom: '12px' }}>Step {i + 1}</div>
                        <CopyableField label={`Direction: [${step.side}]`} value={step.hash} isMonospace={true} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ACTION */}
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '24px' }}>
            <button 
              onClick={handleDownloadPDF} 
              disabled={isGenerating}
              style={{ 
                background: '#1E3A8A', 
                color: '#FFFFFF', 
                border: 'none', 
                borderRadius: '8px', 
                padding: '16px 40px', 
                fontSize: '16px', 
                fontWeight: 700, 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                cursor: isGenerating ? 'not-allowed' : 'pointer', 
                transition: 'background 0.2s',
                opacity: isGenerating ? 0.8 : 1,
                boxShadow: '0 4px 12px rgba(30, 58, 138, 0.2)'
              }}
              onMouseOver={(e) => { if (!isGenerating) e.currentTarget.style.background = '#1e40af'; }}
              onMouseOut={(e) => { if (!isGenerating) e.currentTarget.style.background = '#1E3A8A'; }}
              onMouseDown={(e) => { if (!isGenerating) e.currentTarget.style.transform = 'scale(0.98)'; }}
              onMouseUp={(e) => { if (!isGenerating) e.currentTarget.style.transform = 'scale(1)'; }}
            >
              <Download size={20} />
              {isGenerating ? 'Generating PDF...' : 'Download Receipt PDF'}
            </button>
          </div>

        </div>

        {/* FOOTER */}
        <div style={{ padding: '24px', background: '#F8FAFC', borderTop: '1px solid #E2E8F0', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#64748B', fontSize: '14px', fontWeight: 600 }}>
          <Lock size={16} /> Secure • Tamper-Evident • Verified
        </div>
      </div>
      
      {/* Simple inline animation style for the success checkmark */}
      <style>{`
        @keyframes scaleIn {
          0% { transform: scale(0.8); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
