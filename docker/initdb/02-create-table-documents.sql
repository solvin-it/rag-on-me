CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; 

CREATE TABLE IF NOT EXISTS documents (
  langchain_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  content      TEXT,
  embedding    vector(1536),
  source       TEXT,
  metadata     JSONB
);