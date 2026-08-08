import type { Receipt } from "../../api/api";
import { CheckCircle, ShieldCheck, Download, Copy } from "lucide-react";

export function ReceiptCard({ receipt, paperHash }: { receipt: Receipt; paperHash: string }) {
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
              <dd className="mono" style={{ fontSize: '1.1rem' }}>#{receipt.leaf_index}</dd>

              <dt>Paper Hash</dt>
              <dd className="mono">{paperHash}</dd>

              <dt>Ledger Root</dt>
              <dd className="mono">{receipt.root}</dd>
              
              <dt>Verification Status</dt>
              <dd>
                <span className="tag" style={{ background: 'var(--success)', color: '#fff' }}>Verified</span>
              </dd>
            </dl>

            <details style={{ marginTop: '2rem', background: '#F8FAFC', padding: '1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 600, color: 'var(--text)' }}>
                View Merkle Inclusion Proof ({receipt.path.length} steps)
              </summary>
              <ol className="proof">
                {receipt.path.map((step: { side: "L" | "R"; hash: string }, i: number) => (
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
            <button className="primary" onClick={() => window.print()}>
              <Download size={16} /> Download PDF
            </button>
          </div>
        </div>
      </main>
    </>
  );
}
