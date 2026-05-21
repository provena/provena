# Local Identifier Service

On-prem replacement for the ARDC Handle Service. Provides handle minting and resolution via PostgreSQL.

## Endpoints

- `POST /handle/mint` - Mint a new handle (compatible with registry-api)
- `PUT /handle/modify_by_index` - Update handle value at index
- `GET /handle/get?id=...` - Get handle details
- `GET /handle/list` - List all handle IDs
- `GET /resolve/{handle_id}` - Public redirect to resolved URL or registry landing page

## Setup

1. Create PostgreSQL database
2. Set `DATABASE_URL` in `.env`
3. Run `python scripts/init_db.py` to create schema
4. Start with `uvicorn main:app --reload`

## Docker

```bash
docker build -t local-identifier-service .
docker run -p 8000:8000 -e DATABASE_URL=postgresql://... local-identifier-service
```
