import { useState, useEffect, useRef } from "react";

/**
 * useTabOwnership implements a lightweight frontend-only heartbeat mechanism 
 * to detect if an exam session is already active in another browser tab.
 * 
 * Key Features:
 * - Differentiates between a page reload (allowed) and a duplicate tab (blocked).
 * - Differentiates between an active owner and a dead/closed owner (reclaims).
 * - Resolves collisions cleanly if multiple blocked tabs try to claim a dead session.
 */
export function useTabOwnership(sessionId: string) {
  const [hasOwnership, setHasOwnership] = useState<boolean>(true);
  
  const isOwnerRef = useRef(true);
  const ownerSinceRef = useRef(0);
  
  // Persist the instanceId across Strict Mode dual-mounts
  const instanceIdRef = useRef(crypto.randomUUID());
  const instanceId = instanceIdRef.current;

  useEffect(() => {
    const lsKey = `exam_owner_${sessionId}`;
    const unloadKey = `exam_unload_${sessionId}`;
    
    const channelName = `exam-session-${sessionId}`;
    const channel = new BroadcastChannel(channelName);

    // 1. Initial Assessment
    const rawOwner = localStorage.getItem(lsKey);
    let assumeOwnership = true;

    if (rawOwner) {
      try {
        const owner = JSON.parse(rawOwner);
        const ageMs = Date.now() - owner.timestamp;
        const lastUnloaded = sessionStorage.getItem(unloadKey);

        if (ageMs < 5000) {
          if (owner.instanceId === instanceId) {
            // We are already the owner! (e.g. Strict Mode second mount reconnecting to its own heartbeat)
            assumeOwnership = true;
          } else if (lastUnloaded === owner.instanceId) {
            // Definitively a reload of the active owner tab! 
            // The active owner was exactly the instance that just unloaded in THIS tab's sessionStorage.
            assumeOwnership = true;
          } else {
            // The active owner is in another tab (e.g. duplicate tab, or genuinely different tab)
            assumeOwnership = false;
          }
        }
      } catch(e) {}
    }

    setHasOwnership(assumeOwnership);
    isOwnerRef.current = assumeOwnership;
    if (assumeOwnership) {
      ownerSinceRef.current = Date.now();
    }

    // Always clear the unload key immediately so it can't be falsely reused on duplicate.
    sessionStorage.removeItem(unloadKey);

    // 2. Broadcast Communication
    channel.onmessage = (event) => {
      const msg = event.data;
      if (msg.type === "CLAIM") {
        if (isOwnerRef.current) {
          // Tell the claimant that we are already the owner
          channel.postMessage({ 
            type: "ALIVE", 
            instanceId, 
            ownerSince: ownerSinceRef.current 
          });
        }
      } else if (msg.type === "ALIVE") {
        // Someone else claims to be the owner. 
        // Resolve collisions: Older owner wins. Tie-break using instanceId string comparison.
        const theirTime = msg.ownerSince;
        const myTime = ownerSinceRef.current;
        if (theirTime < myTime || (theirTime === myTime && msg.instanceId > instanceId)) {
          setHasOwnership(false);
          isOwnerRef.current = false;
        }
      }
    };

    if (assumeOwnership) {
      channel.postMessage({ type: "CLAIM", instanceId });
      localStorage.setItem(lsKey, JSON.stringify({ instanceId, timestamp: Date.now() }));
    }

    // 3. Heartbeat & Recovery Loop
    const interval = setInterval(() => {
      if (isOwnerRef.current) {
        // We are the owner, keep the heartbeat alive
        localStorage.setItem(lsKey, JSON.stringify({ instanceId, timestamp: Date.now() }));
      } else {
        // We are NOT the owner. Check if the current owner died (tab closed/crashed).
        const currOwnerStr = localStorage.getItem(lsKey);
        if (currOwnerStr) {
          try {
            const currOwner = JSON.parse(currOwnerStr);
            const ageMs = Date.now() - currOwner.timestamp;
            if (ageMs > 5000) {
              // The owner's heartbeat is stale. We can claim ownership!
              setHasOwnership(true);
              isOwnerRef.current = true;
              ownerSinceRef.current = Date.now();
              channel.postMessage({ type: "CLAIM", instanceId });
              localStorage.setItem(lsKey, JSON.stringify({ instanceId, timestamp: Date.now() }));
            }
          } catch(e) {}
        } else {
          // No owner record at all, claim it
          setHasOwnership(true);
          isOwnerRef.current = true;
          ownerSinceRef.current = Date.now();
          channel.postMessage({ type: "CLAIM", instanceId });
          localStorage.setItem(lsKey, JSON.stringify({ instanceId, timestamp: Date.now() }));
        }
      }
    }, 1500); // 1.5 second interval

    // 4. Teardown
    const handleBeforeUnload = () => {
      if (isOwnerRef.current) {
        // Mark that THIS specific instance is unloading in THIS tab's sessionStorage.
        // If the user reloads, this sessionStorage survives.
        // If the user duplicates the tab, beforeunload never fires for the cloned tab.
        sessionStorage.setItem(unloadKey, instanceId);
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      clearInterval(interval);
      channel.close();
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [sessionId]);

  return hasOwnership;
}
