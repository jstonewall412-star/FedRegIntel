CREATE TABLE IF NOT EXISTS subscribers (
  email TEXT PRIMARY KEY,
  subscribed_at TEXT NOT NULL,
  consent_version TEXT NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending-launch-unverified'
);
