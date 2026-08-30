-- Portable Memory OS: canonical PostgreSQL schema (v1)
-- pgvector is optional for Phase 2 embeddings.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE sources (
  source_id bigserial PRIMARY KEY,
  source_type text NOT NULL,
  source_name text NOT NULL,
  source_uri text,
  source_sha256 char(64),
  imported_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(source_type, source_name, source_sha256)
);

CREATE TABLE conversations (
  conversation_id text PRIMARY KEY,
  source_id bigint REFERENCES sources(source_id),
  title text,
  create_time timestamptz,
  update_time timestamptz,
  current_node_id text,
  source_conversation_sha256 char(64) NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE nodes (
  node_id text NOT NULL,
  conversation_id text NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  parent_node_id text,
  has_message boolean NOT NULL,
  children text[] NOT NULL DEFAULT '{}',
  is_current_node boolean NOT NULL DEFAULT false,
  source_node_sha256 char(64) NOT NULL,
  PRIMARY KEY(conversation_id, node_id)
);
CREATE INDEX nodes_conversation_idx ON nodes(conversation_id);
CREATE INDEX nodes_parent_idx ON nodes(parent_node_id);

CREATE TABLE messages (
  message_id text NOT NULL,
  node_id text NOT NULL,
  conversation_id text NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  parent_node_id text,
  role text,
  author_name text,
  create_time timestamptz,
  update_time timestamptz,
  status text,
  recipient text,
  weight double precision,
  end_turn boolean,
  content_type text,
  text_exact text NOT NULL DEFAULT '',
  text_sha256 char(64) NOT NULL,
  content jsonb NOT NULL,
  metadata jsonb NOT NULL,
  message_raw jsonb NOT NULL,
  source_message_sha256 char(64) NOT NULL,
  PRIMARY KEY(conversation_id, message_id),
  FOREIGN KEY(conversation_id, node_id) REFERENCES nodes(conversation_id, node_id) ON DELETE CASCADE,
  search_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(text_exact,''))) STORED
);
CREATE INDEX messages_conversation_time_idx ON messages(conversation_id, create_time);
CREATE INDEX messages_search_idx ON messages USING gin(search_tsv);
CREATE INDEX messages_text_trgm_idx ON messages USING gin(text_exact gin_trgm_ops);

CREATE TABLE message_edges (
  conversation_id text NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  parent_node_id text NOT NULL,
  child_node_id text NOT NULL,
  edge_type text NOT NULL DEFAULT 'PARENT_OF',
  PRIMARY KEY(conversation_id, parent_node_id, child_node_id)
);

CREATE TABLE attachments (
  attachment_id bigserial PRIMARY KEY,
  conversation_id text NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  message_id text NOT NULL,
  node_id text NOT NULL,
  kind text NOT NULL,
  ref text NOT NULL,
  metadata jsonb,
  UNIQUE(conversation_id, message_id, kind, ref),
  FOREIGN KEY(conversation_id, message_id) REFERENCES messages(conversation_id, message_id) ON DELETE CASCADE,
  FOREIGN KEY(conversation_id, node_id) REFERENCES nodes(conversation_id, node_id) ON DELETE CASCADE
);

-- Phase 2: retrieval chunks. Exact message text remains authoritative.
CREATE TABLE chunks (
  chunk_id bigserial PRIMARY KEY,
  conversation_id text NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  first_message_id text,
  last_message_id text,
  text text NOT NULL,
  source_message_ids text[] NOT NULL,
  char_ranges jsonb NOT NULL,
  embedding vector(1536),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX chunks_conversation_idx ON chunks(conversation_id);
