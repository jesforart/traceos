"""
Idempotent migration to Cognitive Kernel v2.5 with RED TEAM fixes.

RED TEAM FIX #1: Migration idempotence with table signatures.
This migration can be run multiple times safely without corrupting data.
"""

import hashlib
import json
import struct
from typing import Dict, List
from tracememory.models.memory import STYLE_VECTOR_DIM


def compute_table_signature(table_name: str, schema_def: Dict) -> str:
    """
    Compute SHA-256 signature of table schema.

    RED TEAM FIX #1: Prevents corruption from double-runs.
    Each table has a content hash so we can detect if it's already been created correctly.
    """
    schema_json = json.dumps(schema_def, sort_keys=True)
    return hashlib.sha256(f"{table_name}:{schema_json}".encode()).hexdigest()


# Define expected schemas with signatures
TABLE_SCHEMAS = {
    "cognitive_memory_blocks": {
        "signature": None,  # Will be computed
        "schema": """
            CREATE TABLE IF NOT EXISTS cognitive_memory_blocks (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                artifact_id TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                ld_context TEXT,
                derived_from TEXT,
                intent_profile_id TEXT,
                style_dna_id TEXT,
                tags TEXT,
                notes TEXT,
                metadata TEXT,
                UNIQUE(session_id, artifact_id),
                FOREIGN KEY (intent_profile_id) REFERENCES intent_profiles(id),
                FOREIGN KEY (style_dna_id) REFERENCES style_dna(id)
            )
        """,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_cognitive_memory_blocks_session ON cognitive_memory_blocks(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cognitive_memory_blocks_artifact ON cognitive_memory_blocks(artifact_id)",
            "CREATE INDEX IF NOT EXISTS idx_cognitive_memory_blocks_composite ON cognitive_memory_blocks(session_id, artifact_id)"
        ]
    },
    "style_dna": {
        "signature": None,
        "schema": """
            CREATE TABLE IF NOT EXISTS style_dna (
                id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL,
                stroke_dna BLOB,
                image_dna BLOB,
                temporal_dna BLOB,
                created_at TIMESTAMP NOT NULL,
                l2_norm REAL,
                checksum TEXT
            )
        """,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_style_dna_artifact ON style_dna(artifact_id)"
        ]
    },
    "intent_profiles": {
        "signature": None,
        "schema": """
            CREATE TABLE IF NOT EXISTS intent_profiles (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                artifact_id TEXT,
                emotional_register TEXT,
                target_audience TEXT,
                constraints TEXT,
                narrative_prompt TEXT,
                style_keywords TEXT,
                created_at TIMESTAMP NOT NULL,
                source TEXT
            )
        """,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_intent_session ON intent_profiles(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_intent_artifact ON intent_profiles(artifact_id)"
        ]
    },
    "telemetry_chunks": {
        "signature": None,
        "schema": """
            CREATE TABLE IF NOT EXISTS telemetry_chunks (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                artifact_id TEXT,
                parquet_path TEXT NOT NULL,
                chunk_row_count INTEGER NOT NULL,
                total_session_rows INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                schema_version INTEGER DEFAULT 1
            )
        """,
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry_chunks(session_id)"
        ]
    }
}

# Compute signatures
for table_name, config in TABLE_SCHEMAS.items():
    config["signature"] = compute_table_signature(
        table_name,
        {"schema": config["schema"], "indexes": config["indexes"]}
    )


def create_schema_version_table(conn):
    """Create table to track schema versions and table signatures"""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_versions (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)

    # RED TEAM FIX #1: Add table signature tracking
    conn.execute("""
        CREATE TABLE IF NOT EXISTS table_signatures (
            table_name TEXT PRIMARY KEY,
            signature TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def verify_table_signature(conn, table_name: str, expected_sig: str) -> bool:
    """
    Check if table exists with expected signature.

    RED TEAM FIX #1: Prevents re-running migrations that could corrupt data.
    """
    row = conn.execute(
        "SELECT signature FROM table_signatures WHERE table_name = ?",
        (table_name,)
    ).fetchone()

    if row and row[0] == expected_sig:
        return True
    return False


def migrate_to_v2_5(storage):
    """
    Add tables for Cognitive Kernel v2.5 with idempotent safety.

    RED TEAM FIX #1: This migration can be run multiple times safely.

    Args:
        storage: MemoryStorage instance with get_connection() method
    """
    conn = storage.get_connection()

    # Ensure schema tracking exists
    create_schema_version_table(conn)

    # Check if already migrated to v2.5
    current = conn.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0]
    if current and current >= 25:
        print("✓ Already at v2.5 or higher")

        # Verify all table signatures match
        all_valid = True
        for table_name, config in TABLE_SCHEMAS.items():
            if not verify_table_signature(conn, table_name, config["signature"]):
                print(f"⚠️  Warning: {table_name} signature mismatch - may need manual verification")
                all_valid = False

        if all_valid:
            print("✓ All table signatures verified")
        return

    print("🔧 Migrating to v2.5 Cognitive Kernel...")

    # Create each table with signature tracking
    for table_name, config in TABLE_SCHEMAS.items():
        # Skip if already exists with correct signature
        if verify_table_signature(conn, table_name, config["signature"]):
            print(f"✓ {table_name} already exists with correct signature")
            continue

        # Create table
        conn.execute(config["schema"])

        # Create indexes
        for index_sql in config["indexes"]:
            conn.execute(index_sql)

        # Record signature
        conn.execute("""
            INSERT OR REPLACE INTO table_signatures (table_name, signature)
            VALUES (?, ?)
        """, (table_name, config["signature"]))

        print(f"✓ Created {table_name}")

    # Record migration
    conn.execute(
        "INSERT OR IGNORE INTO schema_versions (version, description) VALUES (?, ?)",
        (25, "Cognitive Kernel v2.5: Tri-State Memory with Red Team fixes")
    )

    conn.commit()
    print("✅ Migration to v2.5 complete!")


# Vector serialization helpers
def vector_to_blob(vector: List[float]) -> bytes:
    """
    Convert float list to SQLite BLOB (float32)

    RED TEAM FIX #4: Validates dimension before serialization
    """
    from tracememory.models.memory import validate_vector_dim

    # Validate before storing
    validate_vector_dim(vector, STYLE_VECTOR_DIM)

    return struct.pack(f'{len(vector)}f', *vector)


def blob_to_vector(blob: bytes) -> List[float]:
    """
    Convert SQLite BLOB to float list

    RED TEAM FIX #4: Validates dimension after deserialization
    """
    count = len(blob) // 4  # 4 bytes per float32
    vector = list(struct.unpack(f'{count}f', blob))

    # Validate after loading
    if len(vector) != STYLE_VECTOR_DIM:
        raise ValueError(
            f"Corrupt vector in database: expected {STYLE_VECTOR_DIM} dims, got {len(vector)}"
        )

    return vector
