import type { Receipt } from "../api";

/**
 * The candidate's proof of what they sat.
 *
 * This is the whole accountability story made visible: the paper hash,
 * the Merkle root, and the sibling path that links one to the other.
 * A candidate keeps this and can verify it years later, offline,
 * against the published root.
 *
 * TODO(role 4): print view and QR encoding.
 * TODO(role 1): show the Ed25519 signature once blocks are signed.
 */
export function ReceiptCard({ receipt, paperHash }: { receipt: Receipt; paperHash: string }) {
  return (
    <section className="receipt">
      <h2>Submission receipt</h2>
      <p className="muted">
        Keep this. It proves which paper you sat, without trusting anyone.
      </p>

      <dl>
        <dt>Paper hash</dt>
        <dd className="mono">{paperHash}</dd>

        <dt>Ledger index</dt>
        <dd className="mono">{receipt.leaf_index}</dd>

        <dt>Merkle root</dt>
        <dd className="mono">{receipt.root}</dd>
      </dl>

      <details>
        <summary>Inclusion proof ({receipt.path.length} steps)</summary>
        <ol className="proof">
          {receipt.path.map((step, i) => (
            <li key={i}>
              <span className="tag">{step.side}</span>
              <span className="mono">{step.hash}</span>
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}
