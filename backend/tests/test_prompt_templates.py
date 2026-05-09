import pytest
from datetime import date
from app.nl2sql.prompt_templates import (
    NL2SQL_SYSTEM_PROMPT, FEW_SHOT_EXAMPLES, CORRECT_ERROR_PROMPT
)
from app.core.context import SYSTEM_PROMPT_BOUNDARY


class TestNl2sqlSystemPrompt:
    def test_boundary_included(self):
        assert SYSTEM_PROMPT_BOUNDARY.strip() in NL2SQL_SYSTEM_PROMPT

    def test_placeholders_exist(self):
        assert "__SCHEMA_DESC__" in NL2SQL_SYSTEM_PROMPT
        assert "__CURRENT_DATE__" in NL2SQL_SYSTEM_PROMPT
        assert "__FEW_SHOT_EXAMPLES__" in NL2SQL_SYSTEM_PROMPT
        assert "__USER_QUERY__" in NL2SQL_SYSTEM_PROMPT

    def test_template_replacements(self):
        filled = (NL2SQL_SYSTEM_PROMPT
            .replace("__SCHEMA_DESC__", "test schema")
            .replace("__CURRENT_DATE__", date.today().isoformat())
            .replace("__FEW_SHOT_EXAMPLES__", "examples")
            .replace("__USER_QUERY__", "query"))
        assert "test schema" in filled
        assert date.today().isoformat() in filled
        assert "examples" in filled
        assert "query" in filled
        assert "__SCHEMA_DESC__" not in filled
        assert "__USER_QUERY__" not in filled

    def test_select_only_rule_present(self):
        assert "只生成SELECT语句" in NL2SQL_SYSTEM_PROMPT or "SELECT" in NL2SQL_SYSTEM_PROMPT


class TestFewShotExamples:
    def test_contains_single_box_query(self):
        assert "BC-101" in FEW_SHOT_EXAMPLES
        assert "container_code" in FEW_SHOT_EXAMPLES

    def test_contains_schedule_query(self):
        assert "fact_vessel_schedule" in FEW_SHOT_EXAMPLES
        assert "vessel_name_cn" in FEW_SHOT_EXAMPLES

    def test_contains_aggregation_query(self):
        assert "SUM" in FEW_SHOT_EXAMPLES
        assert "GROUP BY" in FEW_SHOT_EXAMPLES

    def test_contains_join_query(self):
        assert "JOIN" in FEW_SHOT_EXAMPLES

    def test_all_examples_are_select_only(self):
        lines = FEW_SHOT_EXAMPLES.strip().split("\n")
        for line in lines:
            if line.strip().startswith("A:"):
                sql = line.split("A:", 1)[1].strip()
                assert sql.upper().startswith("SELECT"), f"Non-SELECT in example: {sql[:50]}"


class TestCorrectErrorPrompt:
    def test_contains_error_placeholder(self):
        assert "{errors}" in CORRECT_ERROR_PROMPT

    def test_format_with_errors(self):
        text = CORRECT_ERROR_PROMPT.format(errors="禁止使用 INSERT")
        assert "禁止使用 INSERT" in text

    def test_asks_for_correction(self):
        assert "修正" in CORRECT_ERROR_PROMPT
