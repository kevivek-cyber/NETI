import { useState, useEffect, useRef, useCallback } from "react";
import { saveSessionData, loadSessionData } from "../utils/storage";

import { ResponseChainTracker } from "../utils/crypto";
import type { ResponseEvent } from "../api/api";

export type SaveStatus = "Saved" | "Saving..." | "Offline Saved" | "Sync Pending" | "Error";

export interface AutosavePayload {
  answers: Record<string, number>;
  markedForReview: Record<string, boolean>;
  visited: Record<string, boolean>;
  currentQuestionId: string;
  paperHash: string;
  events: ResponseEvent[];
  expectedResponseChain: string;
  fallbackStartTimeMs?: number;
}

export function useAutosave(candidateId: string, payload: Omit<AutosavePayload, "events" | "expectedResponseChain">) {
  const [status, setStatus] = useState<SaveStatus>(navigator.onLine ? "Saved" : "Offline Saved");

  useEffect(() => {
    const handleOnline = () => setStatus(prev => prev === "Offline Saved" ? "Saved" : prev);
    const handleOffline = () => setStatus(prev => prev === "Saved" ? "Offline Saved" : prev);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);
  
  const payloadRef = useRef(payload);
  const isInitialMount = useRef(true);
  
  // Track events and response chain
  const [chainTracker, setChainTracker] = useState<ResponseChainTracker | null>(null);

  // Initialize chain tracker once on mount
  useEffect(() => {
    ResponseChainTracker.create(payload.paperHash).then(tracker => {
      setChainTracker(tracker);
      
      // If we are recovering a session, re-populate tracker
      loadSessionData(`session_${candidateId}`).then((saved: any) => {
        if (saved && saved.paperHash === payload.paperHash && saved.events) {
          tracker.events = saved.events;
          tracker.currentRHex = saved.expectedResponseChain || tracker.currentRHex;
          setChainTracker(tracker); // trigger re-render if needed
        }
      });
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [payload.paperHash, candidateId]);

  useEffect(() => {
    payloadRef.current = payload;
  }, [payload]);

  // Debounced save effect
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    if (!chainTracker) return;

    setStatus("Saving...");
    const timeoutId = setTimeout(async () => {
      try {
        const dataToSave: AutosavePayload = {
          ...payloadRef.current,
          events: chainTracker.events,
          expectedResponseChain: chainTracker.currentRHex,
        };
        
        // Local Persistence (IndexedDB)
        await saveSessionData(`session_${candidateId}`, dataToSave);

        // Backend doesn't have an intermediate sync endpoint right now, so we stay Offline Saved or Saved.
        setStatus(navigator.onLine ? "Saved" : "Offline Saved");
      } catch (err) {
        console.error("Autosave failed", err);
        setStatus("Error");
      }
    }, 1000); 

    return () => clearTimeout(timeoutId);
  }, [
    payload.answers, 
    payload.markedForReview, 
    payload.visited,
    payload.currentQuestionId, 
    candidateId,
    chainTracker
  ]);

  const addAnswerEvent = useCallback(async (question_id: string, selected_option_index: number) => {
    if (!chainTracker) return;
    const event: ResponseEvent = {
      question_id,
      selected_option_index,
      timestamp_iso: new Date().toISOString(),
    };
    await chainTracker.addEvent(event);
    
    // Trigger a forced save cycle
    setStatus("Saving...");
    const dataToSave: AutosavePayload = {
      ...payloadRef.current,
      events: chainTracker.events,
      expectedResponseChain: chainTracker.currentRHex,
    };
    await saveSessionData(`session_${candidateId}`, dataToSave);
    setStatus(navigator.onLine ? "Saved" : "Offline Saved");
  }, [chainTracker, candidateId]);

  return { status, addAnswerEvent, getEvents: () => chainTracker?.events || [], getExpectedChain: () => chainTracker?.currentRHex || "" };
}

export async function restoreSession(candidateId: string): Promise<AutosavePayload | null> {
  return await loadSessionData(`session_${candidateId}`);
}
