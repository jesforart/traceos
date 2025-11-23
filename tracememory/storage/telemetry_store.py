"""
Scalable stroke telemetry storage using Parquet with row-group writer.

RED TEAM FIX #2: Uses row-group writer for scalable appends.
One file per session, multiple row groups per file.

This avoids the dangerous pattern of:
1. Read entire file
2. Append rows
3. Rewrite entire file

Which causes RAM spikes and poor performance on large sessions.
"""

import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from typing import List, Dict, Optional
from tracememory.models.memory import TelemetryChunk, generate_id


class TelemetryStore:
    """
    Stores high-frequency stroke telemetry in Parquet files.

    RED TEAM FIX #2: Uses row-group writer for scalable appends.
    One file per session, multiple row groups per file.
    """

    def __init__(self, base_path: str = "data/telemetry"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Parquet schema for stroke data
        self.schema = pa.schema([
            ('x', pa.float32()),
            ('y', pa.float32()),
            ('pressure', pa.float32()),
            ('timestamp', pa.float64()),
            ('tilt', pa.float32()),
            ('tilt_x', pa.float32()),  # future-proofing
            ('tilt_y', pa.float32()),  # future-proofing
        ])

        # Track open writers for each session (for efficient appends)
        self._writers: Dict[str, pq.ParquetWriter] = {}
        self._row_counts: Dict[str, int] = {}  # Total rows per session

    def save_strokes(
        self,
        session_id: str,
        artifact_id: str,
        strokes: List[Dict]
    ) -> TelemetryChunk:
        """
        Save strokes to Parquet file for this session using row-group writer.

        RED TEAM FIX #2: Scalable append via row groups.
        Each call writes a new row group without reading the entire file.

        Args:
            session_id: Session identifier
            artifact_id: Artifact identifier
            strokes: List of stroke dicts with keys: x, y, p (pressure), t (timestamp), tilt

        Returns:
            TelemetryChunk metadata
        """
        # Build file path
        parquet_path = self.base_path / f"session_{session_id}.parquet"

        # Convert strokes to PyArrow table
        data = {
            'x': [s.get('x', 0.0) for s in strokes],
            'y': [s.get('y', 0.0) for s in strokes],
            'pressure': [s.get('p', 0.5) for s in strokes],
            'timestamp': [s.get('t', 0.0) for s in strokes],
            'tilt': [s.get('tilt', 0.0) for s in strokes],
            'tilt_x': [s.get('tilt_x', 0.0) for s in strokes],
            'tilt_y': [s.get('tilt_y', 0.0) for s in strokes],
        }

        table = pa.table(data, schema=self.schema)

        # Get or create writer for this session
        if session_id not in self._writers:
            # Create new writer
            self._writers[session_id] = pq.ParquetWriter(parquet_path, self.schema)
            self._row_counts[session_id] = 0

        writer = self._writers[session_id]

        # Write new row group (efficient append)
        writer.write_table(table)

        # Update row count
        self._row_counts[session_id] += len(strokes)

        # Create metadata
        chunk = TelemetryChunk(
            session_id=session_id,
            artifact_id=artifact_id,
            parquet_path=str(parquet_path),
            chunk_row_count=len(strokes),  # Rows in THIS write
            total_session_rows=self._row_counts[session_id],  # Total in file
            schema_version=1
        )

        return chunk

    def close_session(self, session_id: str):
        """
        Close the Parquet writer for a session.
        Call this when a session ends to flush and release resources.
        """
        if session_id in self._writers:
            self._writers[session_id].close()
            del self._writers[session_id]
            del self._row_counts[session_id]

    def load_strokes(self, chunk: TelemetryChunk) -> List[Dict]:
        """Load strokes from Parquet file"""
        table = pq.read_table(chunk.parquet_path)
        df = table.to_pandas()

        return df.to_dict('records')

    def load_session_strokes(self, session_id: str) -> Optional[List[Dict]]:
        """Load all strokes for an entire session"""
        parquet_path = self.base_path / f"session_{session_id}.parquet"

        if not parquet_path.exists():
            return None

        table = pq.read_table(parquet_path)
        df = table.to_pandas()

        return df.to_dict('records')

    def __del__(self):
        """Cleanup: close all open writers"""
        for writer in self._writers.values():
            try:
                writer.close()
            except:
                pass
