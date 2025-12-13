"""
Tests for input validators.
"""
import pytest
from app.utils.validators import (
    sanitize_user_input,
    validate_schema,
    validate_answers,
    validate_file_upload,
)


class TestSanitizeUserInput:
    def test_removes_html_tags(self):
        result = sanitize_user_input("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "Hello" in result

    def test_normalizes_whitespace(self):
        result = sanitize_user_input("Hello    world\n\ntest")
        assert result == "Hello world test"

    def test_truncates_long_input(self):
        long_input = "a" * 10000
        result = sanitize_user_input(long_input, max_length=100)
        assert len(result) == 100

    def test_handles_empty_input(self):
        assert sanitize_user_input("") == ""
        assert sanitize_user_input(None) == ""


class TestValidateSchema:
    def test_valid_schema(self):
        schema = {
            "title": "Test Form",
            "description": "A test form",
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {
                        "question": "What is your name?",
                        "required": True
                    }
                }
            ]
        }
        is_valid, error = validate_schema(schema)
        assert is_valid is True
        assert error is None

    def test_invalid_component_type(self):
        schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "invalid-type",
                    "data": {"question": "Test?"}
                }
            ]
        }
        is_valid, error = validate_schema(schema)
        assert is_valid is False
        assert "invalid type" in error.lower()

    def test_duplicate_component_ids(self):
        schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "Q1?"}
                },
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "Q2?"}
                }
            ]
        }
        is_valid, error = validate_schema(schema)
        assert is_valid is False
        assert "duplicate" in error.lower()


class TestValidateAnswers:
    def test_valid_answers(self):
        schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "Name?", "required": True}
                }
            ]
        }
        answers = {"comp_1": "John Doe"}
        is_valid, error = validate_answers(answers, schema)
        assert is_valid is True

    def test_missing_required_answer(self):
        schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "Name?", "required": True}
                }
            ]
        }
        answers = {}
        is_valid, error = validate_answers(answers, schema)
        assert is_valid is False
        assert "required" in error.lower()

    def test_invalid_multiple_choice_answer(self):
        schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "multiple-choice",
                    "data": {
                        "question": "Color?",
                        "options": ["Red", "Blue"],
                        "required": True
                    }
                }
            ]
        }
        answers = {"comp_1": "Green"}
        is_valid, error = validate_answers(answers, schema)
        assert is_valid is False
        assert "invalid option" in error.lower()


class TestValidateFileUpload:
    def test_valid_text_file(self):
        file_info = {
            "name": "test.txt",
            "type": "text",
            "content": "SGVsbG8gV29ybGQ="  # "Hello World" in base64
        }
        is_valid, error = validate_file_upload(file_info)
        assert is_valid is True

    def test_invalid_extension(self):
        file_info = {
            "name": "test.exe",
            "type": "text",
            "content": "SGVsbG8="
        }
        is_valid, error = validate_file_upload(file_info)
        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_missing_name(self):
        file_info = {
            "type": "text",
            "content": "SGVsbG8="
        }
        is_valid, error = validate_file_upload(file_info)
        assert is_valid is False
