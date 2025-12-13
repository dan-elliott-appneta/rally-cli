"""Tests for Rally API helpers."""

import pytest

from rally_tui.services.rally_api import (
    RallyAPIError,
    build_base_url,
    build_fetch_string,
    build_query_string,
    get_entity_type_from_prefix,
    get_url_path,
    parse_query_result,
)


class TestGetEntityTypeFromPrefix:
    """Tests for get_entity_type_from_prefix."""

    def test_user_story(self) -> None:
        assert get_entity_type_from_prefix("US1234") == "HierarchicalRequirement"

    def test_defect(self) -> None:
        assert get_entity_type_from_prefix("DE5678") == "Defect"

    def test_task(self) -> None:
        assert get_entity_type_from_prefix("TA9012") == "Task"

    def test_test_case(self) -> None:
        assert get_entity_type_from_prefix("TC3456") == "TestCase"

    def test_feature(self) -> None:
        assert get_entity_type_from_prefix("F59625") == "PortfolioItem/Feature"

    def test_lowercase(self) -> None:
        assert get_entity_type_from_prefix("us1234") == "HierarchicalRequirement"

    def test_unknown_prefix(self) -> None:
        assert get_entity_type_from_prefix("XX1234") == "HierarchicalRequirement"


class TestGetUrlPath:
    """Tests for get_url_path."""

    def test_hierarchical_requirement(self) -> None:
        assert get_url_path("HierarchicalRequirement") == "hierarchicalrequirement"

    def test_defect(self) -> None:
        assert get_url_path("Defect") == "defect"

    def test_portfolio_item_feature(self) -> None:
        assert get_url_path("PortfolioItem/Feature") == "portfolioitem/feature"

    def test_unknown_type(self) -> None:
        assert get_url_path("UnknownType") == "unknowntype"


class TestBuildFetchString:
    """Tests for build_fetch_string."""

    def test_hierarchical_requirement(self) -> None:
        result = build_fetch_string("HierarchicalRequirement")
        assert "FormattedID" in result
        assert "Name" in result
        assert "FlowState" in result

    def test_defect(self) -> None:
        result = build_fetch_string("Defect")
        assert "FormattedID" in result
        assert "State" in result

    def test_with_extra_fields(self) -> None:
        result = build_fetch_string("HierarchicalRequirement", ["CustomField"])
        assert "CustomField" in result

    def test_unknown_type(self) -> None:
        result = build_fetch_string("UnknownType")
        assert "ObjectID" in result
        assert "Name" in result


class TestBuildQueryString:
    """Tests for build_query_string."""

    def test_empty(self) -> None:
        assert build_query_string([]) == ""

    def test_single_condition(self) -> None:
        assert build_query_string(['(State = "Open")']) == '(State = "Open")'

    def test_two_conditions(self) -> None:
        result = build_query_string(['(State = "Open")', '(Owner = "John")'])
        assert "AND" in result
        assert "(State" in result
        assert "(Owner" in result

    def test_three_conditions(self) -> None:
        result = build_query_string(
            [
                '(State = "Open")',
                '(Owner = "John")',
                '(Project = "Foo")',
            ]
        )
        # Should be nested: (((cond1) AND cond2) AND cond3)
        assert result.count("AND") == 2


class TestBuildBaseUrl:
    """Tests for build_base_url."""

    def test_simple_server(self) -> None:
        result = build_base_url("rally1.rallydev.com")
        assert result == "https://rally1.rallydev.com/slm/webservice/v2.0"

    def test_with_https_prefix(self) -> None:
        result = build_base_url("https://rally1.rallydev.com")
        assert result == "https://rally1.rallydev.com/slm/webservice/v2.0"

    def test_with_http_prefix(self) -> None:
        result = build_base_url("http://rally1.rallydev.com")
        assert result == "https://rally1.rallydev.com/slm/webservice/v2.0"


class TestParseQueryResult:
    """Tests for parse_query_result."""

    def test_query_result_success(self) -> None:
        data = {
            "QueryResult": {
                "Results": [{"Name": "Test"}],
                "TotalResultCount": 1,
                "Errors": [],
                "Warnings": [],
            }
        }
        results, total = parse_query_result(data)
        assert len(results) == 1
        assert results[0]["Name"] == "Test"
        assert total == 1

    def test_query_result_empty(self) -> None:
        data = {
            "QueryResult": {
                "Results": [],
                "TotalResultCount": 0,
                "Errors": [],
                "Warnings": [],
            }
        }
        results, total = parse_query_result(data)
        assert len(results) == 0
        assert total == 0

    def test_query_result_error(self) -> None:
        data = {
            "QueryResult": {
                "Results": [],
                "TotalResultCount": 0,
                "Errors": ["Invalid query"],
                "Warnings": [],
            }
        }
        with pytest.raises(RallyAPIError) as exc_info:
            parse_query_result(data)
        assert "Invalid query" in str(exc_info.value)

    def test_operation_result_success(self) -> None:
        data = {
            "OperationResult": {
                "Object": {"Name": "Created"},
                "Errors": [],
                "Warnings": [],
            }
        }
        results, total = parse_query_result(data)
        assert len(results) == 1
        assert results[0]["Name"] == "Created"

    def test_operation_result_error(self) -> None:
        data = {
            "OperationResult": {
                "Object": None,
                "Errors": ["Permission denied"],
                "Warnings": [],
            }
        }
        with pytest.raises(RallyAPIError) as exc_info:
            parse_query_result(data)
        assert "Permission denied" in str(exc_info.value)

    def test_create_result_success(self) -> None:
        data = {
            "CreateResult": {
                "Object": {"FormattedID": "US1234"},
                "Errors": [],
                "Warnings": [],
            }
        }
        results, total = parse_query_result(data)
        assert len(results) == 1
        assert results[0]["FormattedID"] == "US1234"

    def test_unknown_format(self) -> None:
        data = {"UnknownKey": {}}
        results, total = parse_query_result(data)
        assert len(results) == 0
        assert total == 0


class TestRallyAPIError:
    """Tests for RallyAPIError."""

    def test_str(self) -> None:
        error = RallyAPIError(message="Test error")
        assert str(error) == "Test error"

    def test_with_errors(self) -> None:
        error = RallyAPIError(
            message="Main error",
            errors=["Error 1", "Error 2"],
        )
        assert error.message == "Main error"
        assert len(error.errors) == 2

    def test_with_warnings(self) -> None:
        error = RallyAPIError(
            message="Error",
            warnings=["Warning 1"],
        )
        assert len(error.warnings) == 1
