import { useState, useEffect } from "react";

export type ConnectionStatus = "Connected" | "Reconnecting" | "Offline";

export function useConnectionStatus(): ConnectionStatus {
  const [status, setStatus] = useState<ConnectionStatus>(
    navigator.onLine ? "Connected" : "Offline"
  );

  useEffect(() => {
    const handleOnline = () => setStatus("Connected");
    const handleOffline = () => setStatus("Offline");

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return status;
}
