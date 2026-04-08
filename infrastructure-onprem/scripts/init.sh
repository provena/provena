#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE identifier_db;
    CREATE DATABASE keycloak;
    CREATE DATABASE registry_db;
EOSQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d registry_db -f /docker-entrypoint-initdb.d/init-registry.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d identifier_db <<-EOSQL
    CREATE TABLE IF NOT EXISTS handles (
        id VARCHAR(255) PRIMARY KEY,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS handle_properties (
        handle_id VARCHAR(255) NOT NULL REFERENCES handles(id) ON DELETE CASCADE,
        index_num INTEGER NOT NULL,
        type VARCHAR(50) NOT NULL,
        value TEXT NOT NULL,
        PRIMARY KEY (handle_id, index_num)
    );
EOSQL
