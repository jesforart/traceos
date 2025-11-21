/**
 * useStrokeStorage - IndexedDB storage with versioning
 *
 * IMPROVEMENT #7: IndexedDB persistence
 * IMPROVEMENT #13: Version stored strokes for future-proofing
 */

import { useEffect } from 'react';
import { Stroke } from '../types';

const STORAGE_VERSION = 1;

interface StoredStroke extends Stroke {
  _version: number;
  _profileId?: string;
}

/**
 * Hook to automatically save strokes to IndexedDB
 */
export function useStrokeStorage(strokes: Stroke[]) {
  useEffect(() => {
    const timeout = setTimeout(() => {
      saveStrokesToDB(strokes);
    }, 1000);

    return () => clearTimeout(timeout);
  }, [strokes]);
}

/**
 * Save strokes to IndexedDB with versioning
 */
async function saveStrokesToDB(strokes: Stroke[]): Promise<void> {
  return new Promise(async (resolve, reject) => {
    try {
      const db = await openDB();
      const tx = db.transaction('strokes', 'readwrite');
      const store = tx.objectStore('strokes');

      store.clear();

      // IMPROVEMENT #13: Add version to stored strokes
      for (const stroke of strokes) {
        const versionedStroke: StoredStroke = {
          ...stroke,
          _version: STORAGE_VERSION,
          _profileId: localStorage.getItem('current_profile_id') || undefined
        };
        store.add(versionedStroke);
      }

      tx.oncomplete = () => {
        console.log(`💾 Saved ${strokes.length} strokes (v${STORAGE_VERSION}) to IndexedDB`);
        resolve();
      };

      tx.onerror = () => {
        reject(tx.error);
      };
    } catch (error) {
      console.error('Failed to save strokes:', error);
      reject(error);
    }
  });
}

/**
 * Open IndexedDB database
 */
async function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('TraceOS', STORAGE_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      if (!db.objectStoreNames.contains('strokes')) {
        const store = db.createObjectStore('strokes', { keyPath: 'id' });
        store.createIndex('created_at', 'created_at');
        store.createIndex('version', '_version');
        store.createIndex('profileId', '_profileId');
      }
    };
  });
}

/**
 * Load strokes from IndexedDB with version compatibility check
 */
export async function loadStrokesFromDB(): Promise<Stroke[]> {
  return new Promise(async (resolve, reject) => {
    try {
      const db = await openDB();
      const tx = db.transaction('strokes', 'readonly');
      const store = tx.objectStore('strokes');
      const request = store.getAll();

      request.onsuccess = () => {
        const strokes = request.result as StoredStroke[];

        // IMPROVEMENT #13: Filter by version compatibility
        const compatibleStrokes = strokes.filter(
          (s: StoredStroke) => s._version === STORAGE_VERSION
        );

        console.log(`📂 Loaded ${compatibleStrokes.length} strokes (v${STORAGE_VERSION}) from IndexedDB`);
        resolve(compatibleStrokes);
      };

      request.onerror = () => {
        reject(request.error);
      };
    } catch (error) {
      console.error('Failed to load strokes:', error);
      resolve([]);
    }
  });
}

/**
 * Clear all strokes from IndexedDB
 */
export async function clearStrokesFromDB(): Promise<void> {
  return new Promise(async (resolve, reject) => {
    try {
      const db = await openDB();
      const tx = db.transaction('strokes', 'readwrite');
      const store = tx.objectStore('strokes');
      store.clear();

      tx.oncomplete = () => {
        console.log('🗑️ Cleared all strokes from IndexedDB');
        resolve();
      };

      tx.onerror = () => {
        reject(tx.error);
      };
    } catch (error) {
      console.error('Failed to clear strokes:', error);
      reject(error);
    }
  });
}
