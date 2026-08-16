import type { ReceiptPayload } from "../../api/api";
import { CheckCircle, ShieldCheck, Download, Copy } from "lucide-react";
import jsPDF from "jspdf";

export function ReceiptCard({ receipt, paperHash }: { receipt: ReceiptPayload; paperHash: string }) {
  
  const handleDownloadPDF = () => {
    const doc = new jsPDF();
    const margin = 20;
    const maxWidth = 170; // A4 width is 210, minus 20 margin on both sides
    
    // Title & Branding
    doc.setFontSize(22);
    doc.setTextColor(37, 99, 235); // #2563EB primary
    doc.text("NETI", margin, 30);
    
    doc.setFontSize(14);
    doc.setTextColor(15, 23, 42); // #0F172A
    doc.text("NON-EXPLOITABLE TEST INTEGRITY", margin, 40);
    
    doc.setFontSize(12);
    doc.setTextColor(100, 116, 139); // muted
    doc.text("National Eligibility cum Entrance Test (NEET)", margin, 48);
    
    // Status
    doc.setFontSize(16);
    doc.setTextColor(16, 185, 129); // success
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
    doc.setTextColor(16, 185, 129); // success color
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
    
    receipt.inclusion_proof.path.forEach((step) => {
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
  };

  return (
    <>
      <header className="cbt-header" style={{ marginBottom: '2rem' }}>
        <div className="cbt-header-brand">
          <h1 className="cbt-header-title">NETI</h1>
          <span className="cbt-header-subtitle">| Digital Submission Receipt</span>
        </div>
      </header>
      
      <main style={{ maxWidth: '800px' }}>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          
          <div style={{ background: '#F8FAFC', padding: '2rem', borderBottom: '1px solid var(--border)', textAlign: 'center' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '64px', height: '64px', background: 'var(--success)', borderRadius: '50%', color: '#fff', marginBottom: '1rem' }}>
              <CheckCircle size={32} />
            </div>
            <h2 style={{ color: 'var(--success)', fontSize: '1.5rem', margin: 0 }}>Examination Submitted Successfully</h2>
            <p className="muted" style={{ marginTop: '0.5rem' }}>Your responses have been securely recorded in the tamper-evident ledger.</p>
          </div>

          <div style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)', marginBottom: '1rem' }}>
              <ShieldCheck size={20} />
              <h3 style={{ margin: 0 }}>Cryptographic Proof</h3>
            </div>
            
            <p className="small muted">
              This receipt proves which paper you sat and securely anchors it to the public ledger. You can use this to independently verify your submission.
            </p>

            <dl className="receipt">
              <dt>Receipt ID / Index</dt>
              <dd className="mono" style={{ fontSize: '1.1rem' }}>#{receipt.inclusion_proof.index}</dd>

              <dt>Paper Hash</dt>
              <dd className="mono">{paperHash}</dd>

              <dt>Ledger Root</dt>
              <dd className="mono">{receipt.merkle_root}</dd>
              
              <dt>Verification Status</dt>
              <dd>
                <span className="tag" style={{ background: 'var(--success)', color: '#fff' }}>Verified</span>
              </dd>
            </dl>

            <details style={{ marginTop: '2rem', background: '#F8FAFC', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 600, color: 'var(--text)' }}>
                View Merkle Inclusion Proof ({receipt.inclusion_proof.path.length} steps)
              </summary>
              <ol className="proof">
                {receipt.inclusion_proof.path.map((step: { side: "L" | "R"; hash: string }, i: number) => (
                  <li key={i}>
                    <span className="tag" style={{ background: step.side === 'L' ? '#E2E8F0' : '#CBD5E1' }}>{step.side}</span>
                    <span className="mono">{step.hash}</span>
                  </li>
                ))}
              </ol>
            </details>
          </div>
          
          <div style={{ padding: '1.5rem 2rem', background: '#F1F5F9', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            <button className="secondary" onClick={() => navigator.clipboard.writeText(JSON.stringify({receipt, paperHash}, null, 2))}>
              <Copy size={16} /> Copy Receipt
            </button>
            <button className="primary" onClick={handleDownloadPDF}>
              <Download size={16} /> Download PDF
            </button>
          </div>
        </div>
      </main>
    </>
  );
}
