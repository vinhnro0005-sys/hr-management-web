from fastapi import HTTPException
import sqlparse 
FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", 
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "CREATE"
}

def validate_select_only(sql_query: str) -> None:
    """Kiểm tra AST: Bắt buộc chỉ là lệnh SELECT, không chứa DDL/DML."""
    cleaned_query = sql_query.strip().rstrip(";")
    parsed = sqlparse.parse(cleaned_query)

    if not parsed or len(parsed) != 1:
        raise HTTPException(status_code=400, detail="Cú pháp SQL không hợp lệ.")

    stmt = parsed[0]
    if stmt.get_type() != "SELECT":
        raise HTTPException(status_code=403, detail="Chỉ cho phép truy vấn SELECT đọc dữ liệu.")

    for token in stmt.flatten():
        if token.value.upper() in FORBIDDEN_KEYWORDS:
            raise HTTPException(status_code=403, detail=f"Phát hiện từ khóa nguy hiểm: {token.value}")
