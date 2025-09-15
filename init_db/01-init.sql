-- ==============================================================================
-- Political Intelligence Platform - PostgreSQL Initialization Script
-- ==============================================================================
-- This script sets up the core relational schema, including tables, indexes,
-- foreign keys, views, and PL/pgSQL functions for advanced logic.
-- It will be automatically executed by PostgreSQL upon the first startup.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Extensions
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- pgvector for semantic search

-- ------------------------------------------------------------------------------
-- Schemas for Organization
-- ------------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS legislative;
CREATE SCHEMA IF NOT EXISTS social;
CREATE SCHEMA IF NOT EXISTS semantic;

-- ------------------------------------------------------------------------------
-- Data Definitions (Tables & Types)
-- ------------------------------------------------------------------------------

-- Custom Types for consistency
CREATE TYPE legislative.chamber AS ENUM ('House', 'Senate', 'Joint');
CREATE TYPE legislative.party AS ENUM ('Democrat', 'Republican', 'Independent', 'Other');
CREATE TYPE legislative.vote_position AS ENUM ('Yea', 'Nay', 'Abstain', 'Not Voting');
CREATE TYPE social.platform AS ENUM ('Twitter', 'Facebook', 'Other');

-- Legislators Table
CREATE TABLE IF NOT EXISTS legislative.legislators (
    id VARCHAR(255) PRIMARY KEY, -- bioguideId
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    party legislative.party,
    chamber legislative.chamber,
    state CHAR(2),
    district INT,
    contact_url TEXT,
    social_media_handles JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Committees Table
CREATE TABLE IF NOT EXISTS legislative.committees (
    id VARCHAR(255) PRIMARY KEY, -- committeeId
    name TEXT NOT NULL,
    chamber legislative.chamber,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bills Table
CREATE TABLE IF NOT EXISTS legislative.bills (
    id VARCHAR(255) PRIMARY KEY, -- e.g., 'hr123-118'
    bill_number VARCHAR(255) NOT NULL,
    congress INT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    introduced_date DATE,
    latest_action_date DATE,
    latest_action_text TEXT,
    source_url TEXT,
    raw_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Votes (Roll Call) Table
CREATE TABLE IF NOT EXISTS legislative.votes (
    id VARCHAR(255) PRIMARY KEY, -- e.g., 'rollcall-118-56'
    roll_call_number INT NOT NULL,
    date TIMESTAMPTZ,
    chamber legislative.chamber,
    question TEXT,
    result TEXT,
    bill_id VARCHAR(255) REFERENCES legislative.bills(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Junction table for Legislator Votes
CREATE TABLE IF NOT EXISTS legislative.legislator_votes (
    legislator_id VARCHAR(255) NOT NULL REFERENCES legislative.legislators(id) ON DELETE CASCADE,
    vote_id VARCHAR(255) NOT NULL REFERENCES legislative.votes(id) ON DELETE CASCADE,
    position legislative.vote_position NOT NULL,
    PRIMARY KEY (legislator_id, vote_id)
);

-- Social Media Posts Table
CREATE TABLE IF NOT EXISTS social.posts (
    id VARCHAR(255) PRIMARY KEY, -- e.g., tweet_id
    legislator_id VARCHAR(255) NOT NULL REFERENCES legislative.legislators(id) ON DELETE CASCADE,
    platform social.platform NOT NULL,
    post_text TEXT NOT NULL,
    post_timestamp TIMESTAMPTZ,
    sentiment_score REAL,
    sentiment_label VARCHAR(50)
);

-- Document Embeddings Table (for pgvector)
CREATE TABLE IF NOT EXISTS semantic.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL, -- 'bill_summary', 'post_text', etc.
    text_chunk TEXT,
    embedding vector(768) -- IMPORTANT: Adjust this dimension to match your embedding model
);
COMMENT ON COLUMN semantic.embeddings.embedding IS 'Vector embedding for semantic search. Dimension must match the model output.';

-- ------------------------------------------------------------------------------
-- Indexes for Performance
-- ------------------------------------------------------------------------------
CREATE INDEX idx_legislators_party ON legislative.legislators(party);
CREATE INDEX idx_legislators_state ON legislative.legislators(state);
CREATE INDEX idx_bills_introduced_date ON legislative.bills(introduced_date);
CREATE INDEX idx_votes_bill_id ON legislative.votes(bill_id);
CREATE INDEX idx_posts_legislator_id ON social.posts(legislator_id);
-- HNSW index for fast approximate nearest neighbor search with pgvector
CREATE INDEX idx_embeddings_hnsw ON semantic.embeddings USING hnsw (embedding vector_l2_ops);

-- ------------------------------------------------------------------------------
-- Triggers and Functions (PL/pgSQL)
-- ------------------------------------------------------------------------------

-- Function to automatically update the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for legislators table
CREATE TRIGGER update_legislators_modtime
BEFORE UPDATE ON legislative.legislators
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();

-- ------------------------------------------------------------------------------
-- Views for Simplified Queries
-- ------------------------------------------------------------------------------

-- A view to easily see a legislator's complete voting record
CREATE OR REPLACE VIEW legislative.v_legislator_vote_record AS
SELECT
    l.id AS legislator_id,
    l.first_name,
    l.last_name,
    l.party,
    v.id AS vote_id,
    v.question,
    v.date,
    b.bill_number,
    lv.position
FROM
    legislative.legislators l
JOIN
    legislative.legislator_votes lv ON l.id = lv.legislator_id
JOIN
    legislative.votes v ON lv.vote_id = v.id
LEFT JOIN
    legislative.bills b ON v.bill_id = b.id
ORDER BY
    l.last_name, v.date DESC;

-- A view to summarize voting by party on a specific vote
CREATE OR REPLACE VIEW legislative.v_vote_party_summary AS
SELECT
    v.id AS vote_id,
    v.question,
    v.result,
    l.party,
    lv.position,
    COUNT(*) as vote_count
FROM
    legislative.votes v
JOIN
    legislative.legislator_votes lv ON v.id = lv.vote_id
JOIN
    legislative.legislators l ON lv.legislator_id = l.id
GROUP BY
    v.id, v.question, v.result, l.party, lv.position
ORDER BY
    v.id, l.party, lv.position;

-- ------------------------------------------------------------------------------
-- Backup Script (Conceptual - to be run via pg_dump)
-- ------------------------------------------------------------------------------
-- This is not a SQL script to be run directly, but a command-line example.
--
-- #!/bin/bash
-- # Filename: backup.sh
-- DUMP_FILE="/backups/policydocs_$(date +%Y-%m-%d_%H-%M-%S).sql.gz"
-- pg_dump "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}" | gzip > $DUMP_FILE
-- echo "Backup created at ${DUMP_FILE}"
--
-- # To restore:
-- # gunzip < backup.sql.gz | psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"
--
-- ==============================================================================
-- END OF INITIALIZATION SCRIPT
-- ==============================================================================
