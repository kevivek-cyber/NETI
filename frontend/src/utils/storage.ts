const DB_NAME = "NETI_Exam_DB";
const STORE_NAME = "session_store";
const DB_VERSION = 1;

/**
 * Ensures the IDB is open and the store exists.
 */
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };

    request.onsuccess = (event) => resolve((event.target as IDBOpenDBRequest).result);
    request.onerror = (event) => reject((event.target as IDBOpenDBRequest).error);
  });
}

/**
 * Fallback to localStorage if IDB fails.
 */
function useLocalStorageFallback(key: string, data?: any): any {
  const lsKey = `neti_${key}`;
  if (data !== undefined) {
    try {
      localStorage.setItem(lsKey, JSON.stringify(data));
    } catch (e) {
      console.error("localStorage fallback failed to save", e);
    }
  } else {
    try {
      const val = localStorage.getItem(lsKey);
      return val ? JSON.parse(val) : null;
    } catch (e) {
      console.error("localStorage fallback failed to load", e);
      return null;
    }
  }
}

/**
 * Saves arbitrary data to IndexedDB with a fallback to localStorage.
 */
export async function saveSessionData(key: string, data: any): Promise<void> {
  try {
    if (!window.indexedDB) throw new Error("IDB not supported");
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);
      const req = store.put(data, key);
      req.onsuccess = () => resolve();
      req.onerror = () => {
        useLocalStorageFallback(key, data);
        resolve(); // resolve anyway since fallback handled it
      };
    });
  } catch (e) {
    console.warn("Falling back to localStorage for saveSessionData", e);
    useLocalStorageFallback(key, data);
  }
}

/**
 * Loads arbitrary data from IndexedDB with a fallback to localStorage.
 */
export async function loadSessionData(key: string): Promise<any> {
  try {
    if (!window.indexedDB) throw new Error("IDB not supported");
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(key);
      req.onsuccess = () => {
        if (req.result !== undefined) {
          resolve(req.result);
        } else {
          // If not in IDB, try localStorage just in case it was saved there previously
          resolve(useLocalStorageFallback(key));
        }
      };
      req.onerror = () => {
        resolve(useLocalStorageFallback(key));
      };
    });
  } catch (e) {
    console.warn("Falling back to localStorage for loadSessionData", e);
    return useLocalStorageFallback(key);
  }
}
