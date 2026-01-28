CREATE TABLE IF NOT EXISTS cycles (
  cycle_id TEXT PRIMARY KEY,
  fixture_sha256 TEXT NOT NULL,
  created_utc TEXT NOT NULL,
  unified_manifest_path TEXT NOT NULL,
  phio_coherence_score REAL,
  dd_json TEXT,
  ddr_json TEXT,
  e_json TEXT
);
