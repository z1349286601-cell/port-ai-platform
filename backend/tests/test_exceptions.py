import pytest
from app.core.exceptions import AppException, ERROR_CODES


class TestAppException:
    def test_basic_construction(self):
        exc = AppException(code="TEST_ERR", detail="test error", status_code=400)
        assert exc.code == "TEST_ERR"
        assert exc.detail == "test error"
        assert exc.status_code == 400

    def test_default_status_code(self):
        exc = AppException(code="ERR", detail="error")
        assert exc.status_code == 500

    def test_is_exception_instance(self):
        exc = AppException(code="ERR", detail="error")
        assert isinstance(exc, Exception)

    def test_detail_property_accessible(self):
        exc = AppException(code="ERR", detail="something went wrong")
        assert exc.detail == "something went wrong"
        assert exc.code == "ERR"


class TestErrorCodes:
    def test_all_expected_codes_present(self):
        expected = {
            "LLM_UNAVAILABLE", "EMBEDDING_FAILED", "SQL_GENERATION_FAILED",
            "SQL_EXECUTION_FAILED", "KNOWLEDGE_NOT_FOUND", "SESSION_NOT_FOUND",
            "RATE_LIMIT_EXCEEDED", "INVALID_INPUT", "DOCUMENT_TOO_LARGE",
        }
        assert set(ERROR_CODES.keys()) == expected

    def test_each_code_has_message_and_status(self):
        for code, (message, status) in ERROR_CODES.items():
            assert isinstance(code, str)
            assert isinstance(message, str)
            assert isinstance(status, int)
            assert 200 <= status < 600

    def test_error_codes_are_immutable(self):
        codes_snapshot = dict(ERROR_CODES)
        assert codes_snapshot["SESSION_NOT_FOUND"][1] == 404
        assert codes_snapshot["RATE_LIMIT_EXCEEDED"][1] == 429
