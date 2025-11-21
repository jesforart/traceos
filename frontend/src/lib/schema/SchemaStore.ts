/**
 * Week 3: Design Variation Engine - Schema Store
 *
 * IndexedDB storage for design schemas.
 * Provides CRUD operations with versioning.
 */

import type { BaseSchema, SchemaMetadata } from './types';

const DB_NAME = 'TraceOS_SchemaStore';
const DB_VERSION = 1;
const SCHEMA_STORE = 'schemas';
const METADATA_STORE = 'metadata';

/**
 * Initialize IndexedDB database
 */
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      // Create schemas object store
      if (!db.objectStoreNames.contains(SCHEMA_STORE)) {
        const schemaStore = db.createObjectStore(SCHEMA_STORE, {
          keyPath: 'schema_id'
        });
        schemaStore.createIndex('created_at', 'created_at', { unique: false });
        schemaStore.createIndex('version', 'version', { unique: false });
      }

      // Create metadata object store
      if (!db.objectStoreNames.contains(METADATA_STORE)) {
        const metadataStore = db.createObjectStore(METADATA_STORE, {
          keyPath: 'schema_id'
        });
        metadataStore.createIndex('tags', 'tags', {
          unique: false,
          multiEntry: true
        });
        metadataStore.createIndex('author', 'author', { unique: false });
      }
    };
  });
}

/**
 * Schema Store - Persistent storage
 */
export class SchemaStore {
  /**
   * Save a schema to storage
   */
  async save(schema: BaseSchema): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([SCHEMA_STORE], 'readwrite');
      const store = tx.objectStore(SCHEMA_STORE);

      // Update timestamp
      schema.updated_at = Date.now();

      const request = store.put(schema);

      request.onsuccess = () => {
        console.log(`✅ Saved schema: ${schema.schema_id}`);
        resolve();
      };
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Load a schema by ID
   */
  async load(schema_id: string): Promise<BaseSchema | null> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([SCHEMA_STORE], 'readonly');
      const store = tx.objectStore(SCHEMA_STORE);
      const request = store.get(schema_id);

      request.onsuccess = () => {
        const schema = request.result as BaseSchema | undefined;
        resolve(schema || null);
      };
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * List all schemas
   */
  async list(): Promise<BaseSchema[]> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([SCHEMA_STORE], 'readonly');
      const store = tx.objectStore(SCHEMA_STORE);
      const request = store.getAll();

      request.onsuccess = () => {
        const schemas = request.result as BaseSchema[];
        resolve(schemas);
      };
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Delete a schema
   */
  async delete(schema_id: string): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([SCHEMA_STORE, METADATA_STORE], 'readwrite');

      // Delete from both stores
      const schemaStore = tx.objectStore(SCHEMA_STORE);
      const metadataStore = tx.objectStore(METADATA_STORE);

      schemaStore.delete(schema_id);
      metadataStore.delete(schema_id);

      tx.oncomplete = () => {
        console.log(`🗑️ Deleted schema: ${schema_id}`);
        db.close();
        resolve();
      };
      tx.onerror = () => reject(tx.error);
    });
  }

  /**
   * Save schema metadata
   */
  async saveMetadata(metadata: SchemaMetadata): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([METADATA_STORE], 'readwrite');
      const store = tx.objectStore(METADATA_STORE);
      const request = store.put(metadata);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Load schema metadata
   */
  async loadMetadata(schema_id: string): Promise<SchemaMetadata | null> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([METADATA_STORE], 'readonly');
      const store = tx.objectStore(METADATA_STORE);
      const request = store.get(schema_id);

      request.onsuccess = () => {
        const metadata = request.result as SchemaMetadata | undefined;
        resolve(metadata || null);
      };
      request.onerror = () => reject(request.error);

      tx.oncomplete = () => db.close();
    });
  }

  /**
   * Search schemas by tags
   */
  async searchByTags(tags: string[]): Promise<SchemaMetadata[]> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([METADATA_STORE], 'readonly');
      const store = tx.objectStore(METADATA_STORE);
      const index = store.index('tags');

      const results: SchemaMetadata[] = [];
      const requests = tags.map((tag) => index.getAll(tag));

      Promise.all(
        requests.map(
          (req) =>
            new Promise<void>((res, rej) => {
              req.onsuccess = () => {
                results.push(...(req.result as SchemaMetadata[]));
                res();
              };
              req.onerror = () => rej(req.error);
            })
        )
      ).then(() => {
        // Deduplicate
        const unique = Array.from(
          new Map(results.map((m) => [m.schema_id, m])).values()
        );
        resolve(unique);
      });

      tx.oncomplete = () => db.close();
      tx.onerror = () => reject(tx.error);
    });
  }

  /**
   * Clear all schemas (for testing)
   */
  async clear(): Promise<void> {
    const db = await openDB();

    return new Promise((resolve, reject) => {
      const tx = db.transaction([SCHEMA_STORE, METADATA_STORE], 'readwrite');

      tx.objectStore(SCHEMA_STORE).clear();
      tx.objectStore(METADATA_STORE).clear();

      tx.oncomplete = () => {
        console.log('🧹 Cleared all schemas');
        db.close();
        resolve();
      };
      tx.onerror = () => reject(tx.error);
    });
  }
}

// Singleton instance
export const schemaStore = new SchemaStore();
