from typing import List, Dict, Any
from sqlalchemy import text
from app.core.database import SessionLocal 

def execute_analytics_query(sql_query: str) -> List[Dict[str, Any]]:
    """Chạy câu query trực tiếp qua Session của app."""
    with SessionLocal() as db:
        conn = db.connection().execution_options(timeout=3)
        cursor = conn.execute(text(sql_query))
        return [dict(row._mapping) for row in cursor]