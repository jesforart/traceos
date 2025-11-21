/**
 * Week 5: Style DNA Encoding - Storage Manager
 *
 * Multi-mode storage for DNA sessions.
 * Supports IndexedDB, localStorage, and memory modes.
 */

import { StyleDNAConfig } from '../config';
import type { DNASession, DNAStorageRecord, StrokeDNA, ImageDNA, TemporalDNA } from '../types';
import { ulid } from '../../../utils/ulid';

/**
 * Storage Mode
 */
export type StorageMode = 'indexeddb' | 'localstorage' | 'memory';

/**
 * Storage Backend Interface
 */
export interface StorageBackend {
  initialize(): Promise<void>;
  saveSession(session: DNASession): Promise<void>;
  loadSession(session_id: string): Promise<DNASession | null>;
  deleteSession(session_id: string): Promise<void>;
  listSessions(): Promise<DNASession[]>;
  archiveSession(session_id: string): Promise<void>;
  clear(): Promise<void>;
}

/**
 * DNA Storage Manager
 * Manages persistent storage for DNA sessions
 */
export class DNAStorageManager {
  private backend: StorageBackend;
  private mode: StorageMode;

  constructor(mode: StorageMode = StyleDNAConfig.storage.mode) {
    this.mode = mode;
    this.backend = this.createBackend(mode);
  }

  /**
   * Create storage backend based on mode
   */
  private createBackend(mode: StorageMode): StorageBackend {
    switch (mode) {
      case 'indexeddb':
        return new IndexedDBBackend();
      case 'localstorage':
        return new LocalStorageBackend();
      case 'memory':
        return new MemoryBackend();
    }
  }

  /**
   * Initialize storage
   */
  async initialize(): Promise<void> {
    await this.backend.initialize();
    console.log(`📦 DNA Storage initialized (mode: ${this.mode})`);
  }

  /**
   * Save DNA session
   */
  async saveSession(session: DNASession): Promise<void> {
    await this.backend.saveSession(session);
    console.log(`💾 Session saved: ${session.session_id}`);
  }

  /**
   * Load DNA session
   */
  async loadSession(session_id: string): Promise<DNASession | null> {
    const session = await this.backend.loadSession(session_id);
    if (session) {
      console.log(`📂 Session loaded: ${session_id}`);
    }
    return session;
  }

  /**
   * Delete DNA session
   */
  async deleteSession(session_id: string): Promise<void> {
    await this.backend.deleteSession(session_id);
    console.log(`🗑️  Session deleted: ${session_id}`);
  }

  /**
   * List all sessions
   */
  async listSessions(): Promise<DNASession[]> {
    return await this.backend.listSessions();
  }

  /**
   * Archive old session
   */
  async archiveSession(session_id: string): Promise<void> {
    await this.backend.archiveSession(session_id);
    console.log(`📦 Session archived: ${session_id}`);
  }

  /**
   * Archive sessions older than threshold
   */
  async archiveOldSessions(days: number = StyleDNAConfig.storage.archive_after_days): Promise<number> {
    const sessions = await this.listSessions();
    const threshold = Date.now() - days * 24 * 60 * 60 * 1000;

    let archived_count = 0;
    for (const session of sessions) {
      if (session.started_at < threshold) {
        await this.archiveSession(session.session_id);
        archived_count++;
      }
    }

    console.log(`📦 Archived ${archived_count} old sessions`);
    return archived_count;
  }

  /**
   * Clear all storage
   */
  async clear(): Promise<void> {
    await this.backend.clear();
    console.log('🗑️  Storage cleared');
  }

  /**
   * Get storage statistics
   */
  async getStats(): Promise<{
    total_sessions: number;
    total_strokes: number;
    storage_size_bytes: number;
  }> {
    const sessions = await this.listSessions();
    const total_strokes = sessions.reduce((sum, s) => sum + s.total_strokes, 0);

    // Estimate storage size
    const storage_size_bytes = new Blob([JSON.stringify(sessions)]).size;

    return {
      total_sessions: sessions.length,
      total_strokes,
      storage_size_bytes
    };
  }
}

/**
 * IndexedDB Backend
 */
class IndexedDBBackend implements StorageBackend {
  private db: IDBDatabase | null = null;
  private readonly db_name = 'TraceosDNADB';
  private readonly db_version = 1;

  async initialize(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.db_name, this.db_version);

      request.onerror = () => reject(new Error('Failed to open IndexedDB'));

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Sessions store
        if (!db.objectStoreNames.contains('sessions')) {
          const sessions_store = db.createObjectStore('sessions', { keyPath: 'session_id' });
          sessions_store.createIndex('started_at', 'started_at', { unique: false });
          sessions_store.createIndex('artist_id', 'artist_id', { unique: false });
        }

        // Archives store
        if (!db.objectStoreNames.contains('archives')) {
          db.createObjectStore('archives', { keyPath: 'session_id' });
        }
      };
    });
  }

  async saveSession(session: DNASession): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions'], 'readwrite');
      const store = transaction.objectStore('sessions');
      const request = store.put(session);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to save session'));
    });
  }

  async loadSession(session_id: string): Promise<DNASession | null> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions'], 'readonly');
      const store = transaction.objectStore('sessions');
      const request = store.get(session_id);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(new Error('Failed to load session'));
    });
  }

  async deleteSession(session_id: string): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions'], 'readwrite');
      const store = transaction.objectStore('sessions');
      const request = store.delete(session_id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to delete session'));
    });
  }

  async listSessions(): Promise<DNASession[]> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions'], 'readonly');
      const store = transaction.objectStore('sessions');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error('Failed to list sessions'));
    });
  }

  async archiveSession(session_id: string): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    const session = await this.loadSession(session_id);
    if (!session) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions', 'archives'], 'readwrite');
      const sessions_store = transaction.objectStore('sessions');
      const archives_store = transaction.objectStore('archives');

      // Move to archives
      archives_store.put(session);
      sessions_store.delete(session_id);

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(new Error('Failed to archive session'));
    });
  }

  async clear(): Promise<void> {
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['sessions', 'archives'], 'readwrite');
      const sessions_store = transaction.objectStore('sessions');
      const archives_store = transaction.objectStore('archives');

      sessions_store.clear();
      archives_store.clear();

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(new Error('Failed to clear storage'));
    });
  }
}

/**
 * LocalStorage Backend
 */
class LocalStorageBackend implements StorageBackend {
  private readonly key_prefix = 'traceos_dna_';

  async initialize(): Promise<void> {
    // LocalStorage is always available
  }

  async saveSession(session: DNASession): Promise<void> {
    const key = this.key_prefix + session.session_id;
    localStorage.setItem(key, JSON.stringify(session));
  }

  async loadSession(session_id: string): Promise<DNASession | null> {
    const key = this.key_prefix + session_id;
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : null;
  }

  async deleteSession(session_id: string): Promise<void> {
    const key = this.key_prefix + session_id;
    localStorage.removeItem(key);
  }

  async listSessions(): Promise<DNASession[]> {
    const sessions: DNASession[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.key_prefix)) {
        const data = localStorage.getItem(key);
        if (data) {
          sessions.push(JSON.parse(data));
        }
      }
    }

    return sessions;
  }

  async archiveSession(session_id: string): Promise<void> {
    // For localStorage, archiving just adds a flag
    const session = await this.loadSession(session_id);
    if (session) {
      const archive_key = this.key_prefix + 'archive_' + session_id;
      localStorage.setItem(archive_key, JSON.stringify(session));
      await this.deleteSession(session_id);
    }
  }

  async clear(): Promise<void> {
    const keys_to_remove: string[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this.key_prefix)) {
        keys_to_remove.push(key);
      }
    }

    for (const key of keys_to_remove) {
      localStorage.removeItem(key);
    }
  }
}

/**
 * Memory Backend (for testing)
 */
class MemoryBackend implements StorageBackend {
  private sessions: Map<string, DNASession> = new Map();
  private archives: Map<string, DNASession> = new Map();

  async initialize(): Promise<void> {
    // No initialization needed
  }

  async saveSession(session: DNASession): Promise<void> {
    this.sessions.set(session.session_id, session);
  }

  async loadSession(session_id: string): Promise<DNASession | null> {
    return this.sessions.get(session_id) || null;
  }

  async deleteSession(session_id: string): Promise<void> {
    this.sessions.delete(session_id);
  }

  async listSessions(): Promise<DNASession[]> {
    return Array.from(this.sessions.values());
  }

  async archiveSession(session_id: string): Promise<void> {
    const session = this.sessions.get(session_id);
    if (session) {
      this.archives.set(session_id, session);
      this.sessions.delete(session_id);
    }
  }

  async clear(): Promise<void> {
    this.sessions.clear();
    this.archives.clear();
  }
}

/**
 * Global storage manager instance
 */
export const globalDNAStorage = new DNAStorageManager();
