-- Schema for registry tables (registry, auth, lock)
-- Each logical table gets a physical table with id + data (jsonb)

CREATE TABLE IF NOT EXISTS registry_items (
    id VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_items (
    id VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS lock_items (
    id VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_registry_universal_updated 
    ON registry_items ((data->>'universal_partition_key'), ((data->>'updated_timestamp')::bigint));
CREATE INDEX IF NOT EXISTS idx_registry_subtype_updated 
    ON registry_items ((data->>'item_subtype'), ((data->>'updated_timestamp')::bigint));
CREATE INDEX IF NOT EXISTS idx_registry_approver_release 
    ON registry_items ((data->>'release_approver'), ((data->>'release_timestamp')::bigint));
