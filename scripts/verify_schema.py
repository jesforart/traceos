#!/usr/bin/env python3
"""
Schema Verification Tool for TraceOS Cognitive Kernel v2.6

HARDENING v2.6 - Task 5: CLI tool for verifying database schema integrity.

Usage:
    python scripts/verify_schema.py data/tracememory.db
    python scripts/verify_schema.py data/tracememory.db --strict
"""

import sys
import os
from pathlib import Path

# Add tracememory to path
tracememory_path = Path(__file__).parent.parent / "tracememory"
if str(tracememory_path) not in sys.path:
    sys.path.insert(0, str(tracememory_path))

from tracememory.storage.memory_storage import MemoryStorage
from tracememory.storage.migrations.v2_5_cognitive_kernel import (
    migrate_to_v2_5,
    MigrationSignatureMismatch
)


def print_header():
    """Print tool header"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║ TraceOS Cognitive Kernel v2.6 - Schema Verification Tool     ║")
    print("╠═══════════════════════════════════════════════════════════════╣")
    print("║ HARDENING: Verifies database schema integrity                ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()


def verify_schema(db_path: str, strict: bool = False) -> int:
    """
    Verify database schema signatures.

    Args:
        db_path: Path to SQLite database
        strict: If True, fail on any signature mismatch

    Returns:
        Exit code (0 = success, 1 = schema errors, 2 = unexpected errors)
    """
    print(f"📊 Verifying schema for: {db_path}")
    print()

    if not os.path.exists(db_path):
        print(f"❌ Error: Database file not found: {db_path}")
        print()
        print("   Create the database first by running:")
        print("   python -c 'from tracememory.storage.memory_storage import MemoryStorage; MemoryStorage(\"data/tracememory.db\")'")
        return 2

    try:
        # Initialize storage (will run migration with default non-strict mode)
        storage = MemoryStorage(db_path)

        # Re-run migration in verification mode
        print("🔍 Running signature verification...")
        print()

        if strict:
            print("⚠️  STRICT MODE: Will fail on any signature mismatch")
            print()

        migrate_to_v2_5(storage, strict_signatures=strict)

        print()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║ ✓ Schema Verification PASSED                                 ║")
        print("╠═══════════════════════════════════════════════════════════════╣")
        print("║ All table signatures match expected values.                  ║")
        print("║ Database schema is valid and consistent.                     ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        return 0

    except MigrationSignatureMismatch as e:
        print()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║ ❌ Schema Verification FAILED                                ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        print(str(e))
        print()
        return 1

    except Exception as e:
        print()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║ ❌ Unexpected Error                                          ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 2


def print_usage():
    """Print usage instructions"""
    print("Usage:")
    print("  python scripts/verify_schema.py <db_path>")
    print("  python scripts/verify_schema.py <db_path> --strict")
    print()
    print("Arguments:")
    print("  db_path    Path to SQLite database (e.g., data/tracememory.db)")
    print("  --strict   Fail on any signature mismatch (optional)")
    print()
    print("Examples:")
    print("  python scripts/verify_schema.py data/tracememory.db")
    print("  python scripts/verify_schema.py data/tracememory.db --strict")
    print()


def main():
    """Main entry point"""
    print_header()

    # Parse arguments
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_usage()
        sys.exit(0 if len(sys.argv) < 2 else 0)

    db_path = sys.argv[1]
    strict = "--strict" in sys.argv

    # Run verification
    exit_code = verify_schema(db_path, strict=strict)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
