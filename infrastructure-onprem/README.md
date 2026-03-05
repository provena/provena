# Provena On-Prem Infrastructure

Docker Compose stack for running Provena on-premises with PostgreSQL, MinIO, OpenSearch, Neo4j, Keycloak, and the local identifier service.

## Quick Start

1. From the repo root:
   ```bash
   docker compose -f infrastructure-onprem/docker-compose.yml up -d
   ```

2. Create the MinIO bucket (required for data-store-api):
   ```bash
   docker run --rm --network host minio/mc alias set local http://localhost:9000 minioadmin minioadmin
   docker run --rm --network host minio/mc mb local/provena
   ```

3. Configure Keycloak with your realm and clients.

4. Run the APIs with on-prem config (see .env.example).

## Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Registry, auth, identifier DBs |
| MinIO | 9000, 9001 | S3-compatible object storage |
| OpenSearch | 9200 | Search index |
| Neo4j | 7474, 7687 | Provenance graph |
| Keycloak | 8180 | Authentication |
| Local Identifier Service | 8005 | Handle minting/resolution |

## Configuring APIs for On-Prem

Set these environment variables when running each API:

- **Registry API**: `DB_BACKEND=postgres`, `DATABASE_URL`, `REGISTRY_TABLE_NAME=registry_items`, `AUTH_TABLE_NAME=auth_items`, `LOCK_TABLE_NAME=lock_items`, `HANDLE_API_ENDPOINT=http://localhost:8005`
- **Data Store API**: `STORAGE_BACKEND=minio`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
- **Search API**: `SEARCH_AUTH_TYPE=basic`, `OPENSEARCH_USER`, `OPENSEARCH_PASSWORD`, `SEARCH_DOMAIN`

## Building API Images

From repo root:
```bash
docker build -f registry-api/Dockerfile.server -t provena-registry-api .
docker build -f data-store-api/Dockerfile.server -t provena-data-store-api .
# etc.
```
