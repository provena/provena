# Provena On-Prem Infrastructure

Docker Compose stack for running Provena on-premises with PostgreSQL, MinIO, OpenSearch, Neo4j, Keycloak, and all APIs/UIs.

## Quick Start

1. From the repo root:
   ```bash
   docker compose -f infrastructure-onprem/docker-compose.yml up -d
   ```
   The `minio-init` service automatically creates the `provena` bucket.

2. Configure Keycloak at http://localhost:8180 with realm `provena` and clients.

3. **On-prem host URL**: If the UIs are accessed via a hostname (e.g. `http://rrap1.it.csiro.au`), set in `infrastructure-onprem/.env`:
   - `VITE_APP_BASE_URL=http://rrap1.it.csiro.au`
   - `VITE_KEYCLOAK_REALM=provena` (optional; default is `provena`)
   Then rebuild the UI images so login redirects to your Keycloak:
   ```bash
   docker compose -f infrastructure-onprem/docker-compose.yml build --no-cache landing-portal-ui registry-ui data-store-ui prov-ui
   docker compose -f infrastructure-onprem/docker-compose.yml up -d
   ```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Registry, auth, identifier DBs |
| MinIO | 9000, 9001 | S3-compatible object storage |
| OpenSearch | 9200 | Search index |
| Neo4j | 7474, 7687 | Provenance graph |
| Keycloak | 8180 | Authentication |
| Local Identifier Service | 8005 | Handle minting/resolution |
| Registry API | 8001 | Entity registry |
| Auth API | 8002 | Authentication (requires DynamoDB or Postgres) |
| Data Store API | 8003 | Dataset storage |
| Search API | 8004 | Search |
| Job API | 8006 | Async jobs (requires DynamoDB/SNS) |
| Prov API | 8007 | Provenance graph |
| Registry UI | 3001 | Entity registry UI |
| Data Store UI | 3002 | Dataset UI |
| Prov UI | 3003 | Provenance UI |
| Landing Portal UI | 3004 | Landing page |

## Notes

- **Auth API** and **Job API** require DynamoDB (and SNS for Job) for full functionality. They may fail to start without AWS. For a minimal on-prem setup, start only infrastructure + registry-api + data-store-api + search-api + prov-api + local-identifier-service + UIs.
- **UIs** are built with `VITE_APP_BASE_URL` and `VITE_KEYCLOAK_REALM` from `infrastructure-onprem/.env`; set your host URL and rebuild the UI images so Keycloak and API links are correct.
- Run a subset: `docker compose -f infrastructure-onprem/docker-compose.yml up -d postgres minio opensearch neo4j keycloak local-identifier-service registry-api`
