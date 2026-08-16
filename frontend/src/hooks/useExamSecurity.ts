import { useState, useEffect, useCallback } from "react";

/**
 * useExamSecurity implements browser-based kiosk mode and focus protection.
 * 
 * SECURITY LIMITATION:
 * Browser-based kiosk mode is a deterrent, NOT a true operating-system kiosk.
 * A browser application cannot completely prevent:
 * - OS-level task switching
 * - External devices
 * - Screenshots
 * - Another physical device
 * - Browser process termination
 */
export function useExamSecurity() {
  const [hasLostFocus, setHasLostFocus] = useState(false);

  useEffect(() => {
    const handleContextMenu = (e: MouseEvent) => e.preventDefault();
    const handleCopyPaste = (e: ClipboardEvent) => e.preventDefault();
    const handleSelectStart = (e: Event) => e.preventDefault();
    
    const handleVisibilityChange = () => {
      if (document.hidden) setHasLostFocus(true);
    };
    const handleBlur = () => setHasLostFocus(true);
    
    // Keyboard interceptor (Deterrent only)
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent F12
      if (e.key === "F12") {
        e.preventDefault();
      }
      
      if (e.ctrlKey || e.metaKey) {
        const key = e.key.toLowerCase();
        // Prevent Ctrl+C, Ctrl+X, Ctrl+V, Ctrl+U
        if (key === "c" || key === "x" || key === "v" || key === "u") {
          e.preventDefault();
        }
        // Prevent Ctrl+Shift+I, Ctrl+Shift+J
        if (e.shiftKey && (key === "i" || key === "j")) {
          e.preventDefault();
        }
      }
    };

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = ''; // Standard way to trigger browser's exit warning
    };

    document.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('copy', handleCopyPaste);
    document.addEventListener('cut', handleCopyPaste);
    document.addEventListener('paste', handleCopyPaste);
    document.addEventListener('selectstart', handleSelectStart);
    document.addEventListener('keydown', handleKeyDown);
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('copy', handleCopyPaste);
      document.removeEventListener('cut', handleCopyPaste);
      document.removeEventListener('paste', handleCopyPaste);
      document.removeEventListener('selectstart', handleSelectStart);
      document.removeEventListener('keydown', handleKeyDown);
      
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  const clearFocusLoss = useCallback(() => {
    setHasLostFocus(false);
  }, []);

  const enterFullscreen = useCallback(async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
      }
    } catch (e) {
      console.warn("Fullscreen permission denied or unsupported. The exam will continue normally.", e);
    }
  }, []);

  return {
    hasLostFocus,
    clearFocusLoss,
    enterFullscreen
  };
}
