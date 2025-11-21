/**
 * Generate ULID (Universally Unique Lexicographically Sortable Identifier)
 */
export function ulid(): string {
  const timestamp = Date.now();
  const randomness = Math.random().toString(36).substring(2, 15);
  return `${timestamp.toString(36)}_${randomness}`;
}
