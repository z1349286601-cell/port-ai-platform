import pytest
from app.nl2sql.sql_validator import SQLValidator, ValidationResult


class TestSQLValidatorValidate:
    def setup_method(self):
        self.validator = SQLValidator()

    def test_empty_sql_returns_invalid(self):
        result = self.validator.validate("")
        assert not result.is_valid
        assert any("为空" in e for e in result.errors)

    def test_none_sql_returns_invalid(self):
        result = self.validator.validate(None)
        assert not result.is_valid

    def test_whitespace_only_returns_invalid(self):
        result = self.validator.validate("   ")
        assert not result.is_valid

    def test_not_select_returns_invalid(self):
        result = self.validator.validate("EXPLAIN SELECT * FROM t")
        assert not result.is_valid
        assert any("只允许SELECT" in e for e in result.errors)

    def test_insert_blocked(self):
        result = self.validator.validate("INSERT INTO t VALUES (1)")
        assert not result.is_valid
        assert any("INSERT" in e for e in result.errors)

    def test_update_blocked(self):
        result = self.validator.validate("UPDATE t SET a=1")
        assert not result.is_valid

    def test_delete_blocked(self):
        result = self.validator.validate("DELETE FROM t")
        assert not result.is_valid

    def test_drop_blocked(self):
        result = self.validator.validate("SELECT * FROM t; DROP TABLE t")
        assert not result.is_valid

    def test_alter_blocked(self):
        result = self.validator.validate("ALTER TABLE t ADD COLUMN x")
        assert not result.is_valid

    def test_create_blocked(self):
        result = self.validator.validate("CREATE TABLE t (a int)")
        assert not result.is_valid

    def test_pragma_blocked(self):
        result = self.validator.validate("PRAGMA table_info(t)")
        assert not result.is_valid

    def test_attach_blocked(self):
        result = self.validator.validate("ATTACH DATABASE 'x.db' AS x")
        assert not result.is_valid

    def test_dangerous_function_sqlite_version_blocked(self):
        result = self.validator.validate("SELECT sqlite_version()")
        assert not result.is_valid
        assert any("危险函数" in e for e in result.errors)

    def test_dangerous_function_load_extension_blocked(self):
        result = self.validator.validate("SELECT load_extension('/tmp/evil.so')")
        assert not result.is_valid

    def test_dangerous_function_readfile_blocked(self):
        result = self.validator.validate("SELECT readfile('/etc/passwd')")
        assert not result.is_valid

    def test_multi_statement_semicolons_blocked(self):
        result = self.validator.validate("SELECT * FROM a; SELECT * FROM b")
        assert not result.is_valid
        assert any("多语句" in e for e in result.errors)

    def test_trailing_semicolon_allowed(self):
        result = self.validator.validate("SELECT * FROM t;")
        assert result.is_valid

    def test_trailing_semicolons_allowed(self):
        result = self.validator.validate("SELECT * FROM t;;;")
        assert result.is_valid

    def test_unbalanced_parentheses_blocked(self):
        result = self.validator.validate("SELECT * FROM t WHERE (a = 1")
        assert not result.is_valid
        assert any("括号不匹配" in e for e in result.errors)

    def test_balanced_parentheses_valid(self):
        result = self.validator.validate("SELECT * FROM t WHERE (a = 1) AND (b = 2)")
        assert result.is_valid

    def test_valid_simple_select(self):
        result = self.validator.validate("SELECT * FROM fact_container")
        assert result.is_valid

    def test_valid_select_with_join(self):
        result = self.validator.validate(
            "SELECT v.name FROM fact_vessel_schedule vs JOIN dim_vessel v ON vs.code = v.code"
        )
        assert result.is_valid

    def test_valid_select_with_functions(self):
        result = self.validator.validate("SELECT COUNT(*), SUM(amount) FROM t")
        assert result.is_valid

    def test_valid_select_with_subquery(self):
        result = self.validator.validate("SELECT * FROM (SELECT * FROM t)")
        assert result.is_valid

    def test_case_insensitive_keyword_detection(self):
        result = self.validator.validate("insert into t values (1)")
        assert not result.is_valid

    def test_errors_accumulate_multiple_violations(self):
        result = self.validator.validate("INSERT INTO t VALUES (1); DELETE FROM t")
        assert len(result.errors) >= 2


class TestValidationResult:
    def test_valid_result(self):
        r = ValidationResult(is_valid=True, errors=[])
        assert r.is_valid

    def test_invalid_result_with_errors(self):
        r = ValidationResult(is_valid=False, errors=["bad sql"])
        assert not r.is_valid
        assert "bad sql" in r.errors
