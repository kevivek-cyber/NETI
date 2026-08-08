import { useState, useEffect, useRef } from "react";
import { saveSessionData, loadSessionData } from "../utils/storage";
import { apiMocks } from "../api/api-mocks";
import { useConnectionStatus } from "./useConnectionStatus";

export type SaveStatus = "Saved" | "Saving..." | "Offline Saved" | "Sync Pending" | "Error";

export interface AutosavePayload {
  answers: Record<number, number>;
  markedForReview: Record<number, boolean>;
  visited: Record<number, boolean>;
  currentQuestion: number;
  paperHash: string;
}

export function useAutosave(candidateId: string, payload: AutosavePayload) {
  const [status, setStatus] = useState<SaveStatus>("Saved");
  const connectionStatus = useConnectionStatus();
  
  // Use a ref to always have the latest payload for the debounced save
  const payloadRef = useRef(payload);
  const isInitialMount = useRef(true);
  
  useEffect(() => {
    payloadRef.current = payload;
  }, [payload]);

  // Debounced save effect
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    setStatus("Saving...");
    const timeoutId = setTimeout(async () => {
      try {
        const dataToSave = payloadRef.current;
        
        // 1. Local Persistence (IndexedDB with localStorage fallback)
        await saveSessionData(`session_${candidateId}`, dataToSave);

        // 2. Backend Synchronization
        if (connectionStatus === "Connected") {
          await apiMocks.syncSession(candidateId, dataToSave);
          setStatus("Saved");
        } else {
          setStatus("Offline Saved");
        }
      } catch (err) {
        console.error("Autosave failed", err);
        setStatus("Error");
      }
    }, 1000); // 1-second debounce to avoid spamming the DB/Network

    return () => clearTimeout(timeoutId);
  }, [
    payload.answers, 
    payload.markedForReview, 
    payload.visited,
    payload.currentQuestion, 
    candidateId
  ]);

  // Sync when connection is restored
  useEffect(() => {
    if (connectionStatus === "Connected" && (status === "Offline Saved" || status === "Sync Pending" || status === "Error")) {
      setStatus("Saving...");
      apiMocks.syncSession(candidateId, payloadRef.current)
        .then(() => setStatus("Saved"))
        .catch((err: any) => {
          console.error("Background sync failed", err);
          setStatus("Error");
        });
    }
  }, [connectionStatus]); // Only trigger when connection status changes

  return status;
}

/**
 * Utility to restore a session from IndexedDB/localStorage before mounting the exam client.
 */
export async function restoreSession(candidateId: string): Promise<AutosavePayload | null> {
  return await loadSessionData(`session_${candidateId}`);
}
