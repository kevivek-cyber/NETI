import { useState, useEffect, useCallback } from "react";
import { api } from "../api/api";

/**
 * useServerTimer provides a server-authoritative examination countdown.
 * It corrects for local device clock changes/drift by syncing with the server.
 */
export function useServerTimer(
  expiresAtIso: string | undefined,
  fallbackDurationSeconds: number,
  fallbackStartTimeMs: number
) {
  const [timeLeft, setTimeLeft] = useState(fallbackDurationSeconds);
  const [serverDrift, setServerDrift] = useState(0);
  const [isExpired, setIsExpired] = useState(false);
  const [synchronized, setSynchronized] = useState(false);

  // Sync with server time to correct for local clock drift
  const syncTime = useCallback(async () => {
    try {
      const t0 = performance.now();
      const res = await api.getServerTime();
      const t1 = performance.now();
      
      // Calculate one-way latency
      const latency = (t1 - t0) / 2;
      
      // The server's true time when we receive the response
      const estimatedServerTime = res.serverTime + latency;
      
      // Difference between local Date.now() and estimated true server time.
      // A positive drift means the server is AHEAD of the local clock.
      const localTime = Date.now();
      setServerDrift(estimatedServerTime - localTime);
      setSynchronized(true);
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
      // Calculate current authoritative server time based on our drift
      const now = Date.now() + serverDrift;
      
      let remaining = 0;

      if (expiresAtIso) {
        // Use true server-signed expiry
        const expiresAtMs = new Date(expiresAtIso).getTime();
        remaining = Math.max(0, Math.floor((expiresAtMs - now) / 1000));
      } else {
        // Development fallback — not server authoritative.
        // Uses the corrected 'now', but relies on the fallback start time.
        // Note: The system clock changes might still affect this fallback start time depending on browser behaviors.
        const elapsed = Math.floor((now - fallbackStartTimeMs) / 1000);
        remaining = Math.max(0, fallbackDurationSeconds - elapsed);
      }
      
      setTimeLeft(remaining);
      
      if (remaining <= 0) {
        setIsExpired(true);
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [expiresAtIso, fallbackDurationSeconds, fallbackStartTimeMs, serverDrift]);

  const h = Math.floor(timeLeft / 3600);
  const m = Math.floor((timeLeft % 3600) / 60);
  const s = timeLeft % 60;

  const formattedTime = h > 0
    ? `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    : `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;

  const isWarning = timeLeft <= 1800 && timeLeft > 600; // <= 30 mins
  const isDanger = timeLeft <= 600 && timeLeft > 60;   // <= 10 mins
  const isCritical = timeLeft <= 60 && timeLeft > 0;   // <= 1 min

  return {
    timeLeft,
    formattedTime,
    isExpired,
    isWarning,
    isDanger,
    isCritical,
    synchronized,
    isFallback: !expiresAtIso
  };
}
