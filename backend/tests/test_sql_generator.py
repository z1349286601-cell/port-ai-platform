import pytest
from app.nl2sql.sql_generator import SQLGenerator


class TestCleanSql:
    def setup_method(self):
        self.generator = SQLGenerator.__new__(SQLGenerator)

    def test_plain_sql_unchanged(self):
        result = self.generator._clean_sql("SELECT * FROM fact_container")
        assert result == "SELECT * FROM fact_container"

    def test_sql_code_fence_stripped(self):
        result = self.generator._clean_sql("```sql\nSELECT * FROM t\n```")
        assert result == "SELECT * FROM t"

    def test_generic_code_fence_stripped(self):
        result = self.generator._clean_sql("```\nSELECT * FROM t\n```")
        assert result == "SELECT * FROM t"

    def test_trailing_backticks_stripped(self):
        result = self.generator._clean_sql("SELECT * FROM t```")
        assert result == "SELECT * FROM t"

    def test_whitespace_trimmed(self):
        result = self.generator._clean_sql("\n  SELECT * FROM t  \n")
        assert result == "SELECT * FROM t"

    def test_sql_fence_with_leading_whitespace(self):
        result = self.generator._clean_sql("  ```sql\nSELECT * FROM t\n```  ")
        assert result == "SELECT * FROM t"

    def test_only_opening_fence(self):
        result = self.generator._clean_sql("```sql\nSELECT * FROM t")
        assert result == "SELECT * FROM t"

    def test_only_closing_fence(self):
        result = self.generator._clean_sql("SELECT * FROM t```")
        assert result == "SELECT * FROM t"
