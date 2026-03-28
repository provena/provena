"""Handle service logic."""
from sqlalchemy.orm import Session
from sqlalchemy import text
import random
import string
from config import get_settings

settings = get_settings()
PREFIX = settings.handle_prefix


def _generate_id() -> str:
    """Generate a unique handle suffix."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{PREFIX}/{suffix}"


def mint_handle(db: Session, value: str, value_type: str = "URL") -> str:
    """Mint a new handle with initial value at index 1."""
    handle_id = _generate_id()
    db.execute(
        text("""
            INSERT INTO handles (id, created_at)
            VALUES (:id, NOW())
        """),
        {"id": handle_id},
    )
    db.execute(
        text("""
            INSERT INTO handle_properties (handle_id, index_num, type, value)
            VALUES (:handle_id, 1, :type, :value)
        """),
        {"handle_id": handle_id, "type": value_type, "value": value},
    )
    db.commit()
    return handle_id


def modify_by_index(db: Session, handle_id: str, index: int, value: str) -> bool:
    """Update value at given index."""
    result = db.execute(
        text("""
            UPDATE handle_properties
            SET value = :value
            WHERE handle_id = :handle_id AND index_num = :index
        """),
        {"handle_id": handle_id, "index": index, "value": value},
    )
    db.commit()
    return result.rowcount > 0


def get_handle(db: Session, handle_id: str) -> dict | None:
    """Get handle with properties."""
    row = db.execute(
        text("SELECT id FROM handles WHERE id = :id"),
        {"id": handle_id},
    ).fetchone()
    if not row:
        return None
    props = db.execute(
        text("""
            SELECT index_num, type, value
            FROM handle_properties
            WHERE handle_id = :handle_id
            ORDER BY index_num
        """),
        {"handle_id": handle_id},
    ).fetchall()
    return {
        "id": handle_id,
        "properties": [
            {"type": p[1], "value": p[2], "index": p[0]}
            for p in props
        ],
    }


def resolve_url(db: Session, handle_id: str) -> str | None:
    """Resolve handle to URL (value at index 1 if type URL)."""
    row = db.execute(
        text("""
            SELECT value FROM handle_properties
            WHERE handle_id = :handle_id AND type = 'URL'
            ORDER BY index_num
            LIMIT 1
        """),
        {"handle_id": handle_id},
    ).fetchone()
    return row[0] if row else None


def list_handles(db: Session) -> list[str]:
    """List all handle IDs."""
    rows = db.execute(text("SELECT id FROM handles")).fetchall()
    return [r[0] for r in rows]
