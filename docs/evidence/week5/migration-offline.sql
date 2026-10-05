BEGIN;

-- Running upgrade 0002_pdf_documents -> 0003_document_vectors

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

ALTER TABLE documents ADD COLUMN index_status VARCHAR(20) DEFAULT 'pending' NOT NULL;

ALTER TABLE documents ADD COLUMN index_error VARCHAR(500);

ALTER TABLE documents ADD COLUMN index_job_id UUID;

ALTER TABLE documents ADD COLUMN index_started_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE documents ADD COLUMN indexed_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE documents ADD COLUMN chunk_count INTEGER DEFAULT '0' NOT NULL;

ALTER TABLE documents ADD COLUMN embedding_model VARCHAR(200);

ALTER TABLE documents ADD CONSTRAINT ck_documents_index_status CHECK (index_status IN ('pending', 'processing', 'ready', 'failed'));

CREATE TABLE document_chunks (
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    document_id UUID NOT NULL, 
    chunk_index INTEGER NOT NULL, 
    page_number INTEGER NOT NULL, 
    start_char INTEGER NOT NULL, 
    end_char INTEGER NOT NULL, 
    text TEXT NOT NULL, 
    embedding VECTOR(1024) NOT NULL, 
    embedding_model VARCHAR(200) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_document_chunk_index UNIQUE (document_id, chunk_index), 
    FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_document_chunks_document_id ON document_chunks (document_id);

UPDATE alembic_version SET version_num='0003_document_vectors' WHERE alembic_version.version_num = '0002_pdf_documents';

COMMIT;

