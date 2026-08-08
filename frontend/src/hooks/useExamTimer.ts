import { useState, useEffect, useCallback } from "react";
import { apiMocks } from "../api/api-mocks";

/**
 * useExamTimer hooks into the server time to provide a cryptographically 
 * reliable exam countdown, immune to local device clock changes.
 */
export function useExamTimer(durationSeconds: number, startTimeMs: number) {
  const [timeLeft, setTimeLeft] = useState(durationSeconds);
  const [serverDrift, setServerDrift] = useState(0);
  const [isExpired, setIsExpired] = useState(false);

  // Sync with server time to correct for local clock drift
  const syncTime = useCallback(async () => {
    try {
      const t0 = performance.now();
      const res = await apiMocks.getServerTime();
      const t1 = performance.now();
      const latency = (t1 - t0) / 2;
      const estimatedServerTime = res.serverTime + latency;
      
      const localTime = Date.now();
      setServerDrift(estimatedServerTime - localTime);
    } catch (e) {
      console.error("Failed to sync time with server", e);
    }
  }, []);

  // Initial sync and periodic resync every minute
  useEffect(() => {
    syncTime();
    const interval = setInterval(syncTime, 60000);
    return () => clearInterval(interval);
  }, [syncTime]);

  // Tick every second using the corrected time
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now() + serverDrift;
      const elapsed = Math.floor((now - startTimeMs) / 1000);
      const remaining = Math.max(0, durationSeconds - elapsed);
      
      setTimeLeft(remaining);
      
      if (remaining <= 0) {
        setIsExpired(true);
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [durationSeconds, startTimeMs, serverDrift]);

  const h = Math.floor(timeLeft / 3600);
  const m = Math.floor((timeLeft % 3600) / 60);
  const s = timeLeft % 60;

  const formattedTime = h > 0
    ? `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    : `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;

  const isWarning = timeLeft <= 900 && timeLeft > 300; // <= 15 minutes
  const isDanger = timeLeft <= 300 && timeLeft > 60;   // <= 5 minutes
  const isCritical = timeLeft <= 60 && timeLeft > 0;   // <= 1 minute

  return {
    timeLeft,
    formattedTime,
    isExpired,
    isWarning,
    isDanger,
    isCritical,
  };
}
