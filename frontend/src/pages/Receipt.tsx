import { useLocation, Navigate } from "react-router-dom";
import { ReceiptCard } from "../components/cbt/ReceiptCard";
import { Receipt as ReceiptType } from "../api/api";

export function Receipt() {
  const location = useLocation();
  const state = location.state as { receipt: ReceiptType, paperHash: string } | null;

  if (!state || !state.receipt) {
    return <Navigate to="/checkin" replace />;
  }

  return (
    <ReceiptCard receipt={state.receipt} paperHash={state.paperHash} />
  );
}
