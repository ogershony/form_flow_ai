"""Tests for MCP Service."""
import pytest
from unittest.mock import Mock, patch
from app.services.mcp_service import MCPService


class TestMCPService:
    """Test MCP Service functionality."""

    @pytest.fixture
    def mcp_service(self):
        """Create MCP service instance for testing."""
        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            return MCPService()

    def test_validate_schema_basic(self, mcp_service):
        """Test basic schema validation."""
        schema = {
            "title": "Test Form",
            "description": "Test description",
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {
                        "question": "Test question",
                        "required": True
                    }
                }
            ]
        }
        validated = mcp_service._validate_schema(schema)
        assert validated["title"] == "Test Form"
        assert len(validated["components"]) == 1

    def test_validate_schema_missing_fields(self, mcp_service):
        """Test schema validation with missing fields."""
        schema = {}
        validated = mcp_service._validate_schema(schema)
        assert "title" in validated
        assert "description" in validated
        assert "components" in validated
        assert validated["title"] == "Untitled Form"

    def test_validate_schema_multiple_choice(self, mcp_service):
        """Test multiple choice component validation."""
        schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "multiple-choice",
                    "data": {
                        "question": "Choose one",
                        "options": ["A", "B", "C", "D", "E"],  # 5 options, should limit to 4
                        "required": True
                    }
                }
            ]
        }
        validated = mcp_service._validate_schema(schema)
        assert len(validated["components"][0]["data"]["options"]) == 4

    def test_generate_change_description_added(self, mcp_service):
        """Test change description for added components."""
        old_schema = {"components": []}
        new_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "New question", "required": False}
                }
            ]
        }
        description = mcp_service.generate_change_description(old_schema, new_schema)
        assert "Added 1 component(s)" in description

    def test_generate_change_description_removed(self, mcp_service):
        """Test change description for removed components."""
        old_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "Old question", "required": False}
                }
            ]
        }
        new_schema = {"components": []}
        description = mcp_service.generate_change_description(old_schema, new_schema)
        assert "Removed 1 component(s)" in description

    def test_generate_change_description_modified(self, mcp_service):
        """Test change description for modified components."""
        old_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "Old question", "required": False}
                }
            ]
        }
        new_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "New question", "required": True}
                }
            ]
        }
        description = mcp_service.generate_change_description(old_schema, new_schema)
        assert "Modified 1 component(s)" in description

    def test_generate_detailed_diff_added(self, mcp_service):
        """Test detailed diff for added components."""
        old_schema = {"components": []}
        new_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "What is your name?", "required": True}
                }
            ]
        }
        diff = mcp_service.generate_detailed_diff(old_schema, new_schema)

        assert "summary" in diff
        assert "changes" in diff
        assert len(diff["changes"]) == 1
        assert diff["changes"][0]["type"] == "added"
        assert diff["changes"][0]["componentId"] == "comp_1"
        assert "What is your name?" in diff["changes"][0]["details"]

    def test_generate_detailed_diff_removed(self, mcp_service):
        """Test detailed diff for removed components."""
        old_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "multiple-choice",
                    "data": {
                        "question": "Select option",
                        "options": ["A", "B"],
                        "required": False
                    }
                }
            ]
        }
        new_schema = {"components": []}
        diff = mcp_service.generate_detailed_diff(old_schema, new_schema)

        assert len(diff["changes"]) == 1
        assert diff["changes"][0]["type"] == "removed"
        assert "Select option" in diff["changes"][0]["details"]

    def test_generate_detailed_diff_modified(self, mcp_service):
        """Test detailed diff for modified components."""
        old_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "Old question", "required": False}
                }
            ]
        }
        new_schema = {
            "components": [
                {
                    "id": "comp_1",
                    "type": "short-answer",
                    "data": {"question": "New question", "required": True}
                }
            ]
        }
        diff = mcp_service.generate_detailed_diff(old_schema, new_schema)

        assert len(diff["changes"]) == 1
        assert diff["changes"][0]["type"] == "modified"
        assert diff["changes"][0]["before"]["data"]["question"] == "Old question"
        assert diff["changes"][0]["after"]["data"]["question"] == "New question"

    def test_compare_components_question_change(self, mcp_service):
        """Test component comparison for question text changes."""
        old_comp = {
            "type": "short-answer",
            "data": {"question": "Old", "required": False}
        }
        new_comp = {
            "type": "short-answer",
            "data": {"question": "New", "required": False}
        }
        changes = mcp_service._compare_components(old_comp, new_comp)
        assert "Changed question text" in changes

    def test_compare_components_required_change(self, mcp_service):
        """Test component comparison for required status change."""
        old_comp = {
            "type": "short-answer",
            "data": {"question": "Q", "required": False}
        }
        new_comp = {
            "type": "short-answer",
            "data": {"question": "Q", "required": True}
        }
        changes = mcp_service._compare_components(old_comp, new_comp)
        assert "Made required" in changes

    def test_compare_components_options_added(self, mcp_service):
        """Test component comparison for added multiple choice options."""
        old_comp = {
            "type": "multiple-choice",
            "data": {
                "question": "Q",
                "options": ["A", "B"],
                "required": False
            }
        }
        new_comp = {
            "type": "multiple-choice",
            "data": {
                "question": "Q",
                "options": ["A", "B", "C"],
                "required": False
            }
        }
        changes = mcp_service._compare_components(old_comp, new_comp)
        assert any("Added option" in change for change in changes)

    def test_compare_components_options_removed(self, mcp_service):
        """Test component comparison for removed multiple choice options."""
        old_comp = {
            "type": "multiple-choice",
            "data": {
                "question": "Q",
                "options": ["A", "B", "C"],
                "required": False
            }
        }
        new_comp = {
            "type": "multiple-choice",
            "data": {
                "question": "Q",
                "options": ["A", "B"],
                "required": False
            }
        }
        changes = mcp_service._compare_components(old_comp, new_comp)
        assert any("Removed option" in change for change in changes)
