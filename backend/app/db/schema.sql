-- NETI Database Schema (PostgreSQL 15+)
-- Non-negotiable invariant: The ledger is strictly append-only.
-- Enforced via DB level table grants and triggers preventing UPDATE or DELETE.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ledger Blocks Table
CREATE TABLE IF NOT EXISTS candidate_sessions (
    candidate_pseudonym CHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    state VARCHAR(32) NOT NULL DEFAULT 'registered',
    paper_hash_hex CHAR(64),
    receipt JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ledger_blocks (
    height BIGINT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    centre_id VARCHAR(64) NOT NULL,
    block_hash CHAR(64) NOT NULL UNIQUE,
    prev_block_hash CHAR(64) NOT NULL,
    merkle_root CHAR(64) NOT NULL,
    leaf_count INT NOT NULL,
    first_leaf_index INT NOT NULL,
    bank_version_hash CHAR(64) NOT NULL,
    generator_source_hash CHAR(64) NOT NULL,
    blueprint_hash CHAR(64) NOT NULL,
    ceremony_id VARCHAR(64) NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL,
    signature VARCHAR(256) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Ledger Leaves Table (Paper SHA-256 Hashes)
-- NOTE: Absolutely NO question text or paper JSON is stored in this table! Pseudonym & hash only.
CREATE TABLE IF NOT EXISTS ledger_leaves (
    leaf_index BIGINT PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    candidate_pseudonym CHAR(64) NOT NULL,
    leaf_hash CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Ceremony Audit Trail Table
CREATE TABLE IF NOT EXISTS ceremony_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ceremony_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL, -- 'share_presented', 'quorum_reached', 'seed_generated', 'zeroised'
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Submission Audit Receipts Table
CREATE TABLE IF NOT EXISTS submission_receipts (
    candidate_pseudonym CHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    paper_hash CHAR(64) NOT NULL,
    response_chain_digest CHAR(64) NOT NULL,
    receipt_hash CHAR(64) NOT NULL UNIQUE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Trigger Function to Block UPDATE and DELETE Operations
CREATE OR REPLACE FUNCTION raise_append_only_error()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'NETI Ledger Invariant Violation: Ledger tables are append-only. UPDATE and DELETE operations are strictly prohibited.';
END;
$$ LANGUAGE plpgsql;

-- Attach Triggers to Ledger Tables
DROP TRIGGER IF EXISTS enforce_append_only_blocks ON ledger_blocks;
CREATE TRIGGER enforce_append_only_blocks
BEFORE UPDATE OR DELETE ON ledger_blocks
FOR EACH ROW EXECUTE FUNCTION raise_append_only_error();

DROP TRIGGER IF EXISTS enforce_append_only_leaves ON ledger_leaves;
CREATE TRIGGER enforce_append_only_leaves
BEFORE UPDATE OR DELETE ON ledger_leaves
FOR EACH ROW EXECUTE FUNCTION raise_append_only_error();

DROP TRIGGER IF EXISTS enforce_append_only_ceremony ON ceremony_events;
CREATE TRIGGER enforce_append_only_ceremony
BEFORE UPDATE OR DELETE ON ceremony_events
FOR EACH ROW EXECUTE FUNCTION raise_append_only_error();

DROP TRIGGER IF EXISTS enforce_append_only_receipts ON submission_receipts;
CREATE TRIGGER enforce_append_only_receipts
BEFORE UPDATE OR DELETE ON submission_receipts
FOR EACH ROW EXECUTE FUNCTION raise_append_only_error();

-- Revoke permissions at grant level (run for application db user)
-- REVOKE UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM PUBLIC;
