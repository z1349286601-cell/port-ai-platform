import re
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from app.core.database.sqlite_client import SQLiteClient


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


class SQLValidator:
    DANGEROUS_KEYWORDS = [
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b",
        r"\bDROP\b", r"\bALTER\b", r"\bCREATE\b",
        r"\bPRAGMA\b", r"\bATTACH\b", r"\bDETACH\b",
        r"\bREINDEX\b", r"\bVACUUM\b",
    ]

    DANGEROUS_FUNCTIONS = [
        r"sqlite_version\s*\(", r"sqlite_source_id\s*\(",
        r"load_extension\s*\(", r"readfile\s*\(",
        r"writefile\s*\(", r"zeroblob\s*\(",
    ]

    def validate(self, sql: str) -> ValidationResult:
        errors = []

        if not sql or not sql.strip():
            errors.append("SQL语句为空")
            return ValidationResult(is_valid=False, errors=errors)

        sql_upper = sql.upper().strip()

        # Check starts with SELECT
        if not sql_upper.startswith("SELECT"):
            errors.append("只允许SELECT查询语句")

        # Check no dangerous keywords
        for pattern in self.DANGEROUS_KEYWORDS:
            if re.search(pattern, sql, re.IGNORECASE):
                errors.append(f"禁止使用 {pattern.replace(r'\\b', '').strip()} 语句")

        # Check no dangerous functions
        for pattern in self.DANGEROUS_FUNCTIONS:
            if re.search(pattern, sql, re.IGNORECASE):
                errors.append("检测到危险函数调用")

        # Check no multi-statement (semicolons)
        # Allow semicolons only at the very end
        stripped = sql.rstrip(";").strip()
        if ";" in stripped:
            errors.append("禁止多语句查询（包含分号分隔符）")

        # Check balanced parentheses
        if sql.count("(") != sql.count(")"):
            errors.append("括号不匹配")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    async def explain_validate(self, sql: str, db_path: str) -> ValidationResult:
        """Validate SQL by running EXPLAIN against the actual SQLite database."""
        base_result = self.validate(sql)
        if not base_result.is_valid:
            return base_result

        client = SQLiteClient(db_path)
        await client.connect()
        try:
            await client.conn.execute("PRAGMA query_only=ON")
            try:
                await client.conn.execute(f"EXPLAIN {sql}")
            except Exception as e:
                base_result.is_valid = False
                base_result.errors.append(f"SQL语法错误: {str(e)}")
            finally:
                await client.conn.execute("PRAGMA query_only=OFF")
        finally:
            await client.close()

        return base_result
