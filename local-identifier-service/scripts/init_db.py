"""Initialize database schema."""
import sqlalchemy
from config import get_settings

settings = get_settings()
engine = sqlalchemy.create_engine(settings.database_url)

with engine.begin() as conn:
    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS handles (
            id VARCHAR(255) PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """))
    conn.execute(sqlalchemy.text("""
        CREATE TABLE IF NOT EXISTS handle_properties (
            handle_id VARCHAR(255) NOT NULL REFERENCES handles(id) ON DELETE CASCADE,
            index_num INTEGER NOT NULL,
            type VARCHAR(50) NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (handle_id, index_num)
        )
    """))
print("Database initialized.")
