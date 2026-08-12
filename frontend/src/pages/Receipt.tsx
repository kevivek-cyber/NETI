import { useLocation, Navigate } from "react-router-dom";
import { ReceiptCard } from "../components/cbt/ReceiptCard";
import type { ReceiptPayload } from "../api/api";

export function Receipt() {
  const location = useLocation();
  const state = location.state as { receipt: ReceiptPayload, paperHash: string } | null;

  if (!state || !state.receipt) {
    return <Navigate to="/checkin" replace />;
  }

  return (
    <ReceiptCard receipt={state.receipt} paperHash={state.paperHash} />
  );
}
