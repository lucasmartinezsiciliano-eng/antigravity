// Client-side hold for captured face photos so they survive the Stripe redirect.
// Biometric images never reach our server until payment is confirmed — at which
// point capture/[id] reads them back and calls uploadPhotos (which triggers the
// billed analysis). Cleared immediately after a successful upload and on RGPD erase.

const DB_NAME = "visai";
const STORE = "pending_photos";

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE)) {
        req.result.createObjectStore(STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export const photoStore = {
  async save(id: string, files: File[]): Promise<void> {
    const db = await openDB();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.objectStore(STORE).put(files, id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
    db.close();
  },

  async load(id: string): Promise<File[] | null> {
    const db = await openDB();
    const result = await new Promise<File[] | null>((resolve, reject) => {
      const tx = db.transaction(STORE, "readonly");
      const req = tx.objectStore(STORE).get(id);
      req.onsuccess = () => {
        const val = req.result as File[] | undefined;
        resolve(val && val.length ? val : null);
      };
      req.onerror = () => reject(req.error);
    });
    db.close();
    return result;
  },

  async clear(id: string): Promise<void> {
    try {
      const db = await openDB();
      await new Promise<void>((resolve) => {
        const tx = db.transaction(STORE, "readwrite");
        tx.objectStore(STORE).delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = () => resolve();
      });
      db.close();
    } catch { /* best-effort */ }
  },
};
