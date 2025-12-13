"""Rally REST API constants and helper functions.

This module provides constants and utilities for working with the Rally WSAPI.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

# Rally WSAPI version
RALLY_WSAPI_VERSION = "v2.0"

# Default timeout for API requests (seconds)
DEFAULT_TIMEOUT = 30.0

# Maximum concurrent requests (Rally's limit is 12)
MAX_CONCURRENT_REQUESTS = 5

# Maximum page size for queries
MAX_PAGE_SIZE = 200

# Entity type mappings (class name -> URL path)
ENTITY_TYPES = {
    "HierarchicalRequirement": "hierarchicalrequirement",
    "Defect": "defect",
    "Task": "task",
    "TestCase": "testcase",
    "Iteration": "iteration",
    "ConversationPost": "conversationpost",
    "Attachment": "attachment",
    "AttachmentContent": "attachmentcontent",
    "User": "user",
    "PortfolioItem/Feature": "portfolioitem/feature",
}

# Formatted ID prefix to entity type mapping
PREFIX_TO_ENTITY = {
    "US": "HierarchicalRequirement",
    "DE": "Defect",
    "TA": "Task",
    "TC": "TestCase",
    "F": "PortfolioItem/Feature",
}

# Default fields to fetch for each entity type
DEFAULT_FETCH_FIELDS = {
    "HierarchicalRequirement": [
        "FormattedID",
        "Name",
        "FlowState",
        "Owner",
        "Description",
        "Notes",
        "Iteration",
        "PlanEstimate",
        "ObjectID",
        "PortfolioItem",
    ],
    "Defect": [
        "FormattedID",
        "Name",
        "State",
        "Owner",
        "Description",
        "Notes",
        "Iteration",
        "PlanEstimate",
        "ObjectID",
        "PortfolioItem",
    ],
    "Task": [
        "FormattedID",
        "Name",
        "State",
        "Owner",
        "Description",
        "Notes",
        "Iteration",
        "Estimate",
        "ObjectID",
    ],
    "Iteration": [
        "ObjectID",
        "Name",
        "StartDate",
        "EndDate",
        "State",
    ],
    "ConversationPost": [
        "ObjectID",
        "Text",
        "User",
        "CreationDate",
        "Artifact",
    ],
    "Attachment": [
        "ObjectID",
        "Name",
        "Size",
        "ContentType",
    ],
    "User": [
        "ObjectID",
        "DisplayName",
        "UserName",
        "EmailAddress",
    ],
    "PortfolioItem/Feature": [
        "FormattedID",
        "Name",
        "ObjectID",
    ],
}


@dataclass
class RallyAPIError(Exception):
    """Exception raised for Rally API errors."""

    message: str
    errors: list[str] | None = None
    warnings: list[str] | None = None

    def __str__(self) -> str:
        return self.message


def get_entity_type_from_prefix(formatted_id: str) -> str:
    """Determine Rally entity type from formatted ID prefix.

    Args:
        formatted_id: The ticket's formatted ID (e.g., "US1234").

    Returns:
        The Rally entity type name.
    """
    prefix = ""
    for char in formatted_id:
        if char.isdigit():
            break
        prefix += char

    return PREFIX_TO_ENTITY.get(prefix.upper(), "HierarchicalRequirement")


def get_url_path(entity_type: str) -> str:
    """Get the URL path for an entity type.

    Args:
        entity_type: The entity type name (e.g., "HierarchicalRequirement").

    Returns:
        The URL path segment for the entity.
    """
    return ENTITY_TYPES.get(entity_type, entity_type.lower())


def build_fetch_string(entity_type: str, extra_fields: list[str] | None = None) -> str:
    """Build the fetch parameter string for a query.

    Args:
        entity_type: The entity type name.
        extra_fields: Additional fields to fetch beyond defaults.

    Returns:
        Comma-separated string of field names.
    """
    fields = list(DEFAULT_FETCH_FIELDS.get(entity_type, ["ObjectID", "Name"]))
    if extra_fields:
        fields.extend(f for f in extra_fields if f not in fields)
    return ",".join(fields)


def build_query_string(conditions: list[str]) -> str:
    """Build a Rally query string from conditions.

    Rally WSAPI requires nested parentheses for AND queries:
    - Single condition: (condition)
    - Multiple conditions: ((condition1) AND (condition2))

    Args:
        conditions: List of query conditions.

    Returns:
        Properly formatted Rally query string.
    """
    if not conditions:
        return ""

    if len(conditions) == 1:
        return conditions[0]

    # Nest conditions with AND
    result = conditions[0]
    for condition in conditions[1:]:
        result = f"({result} AND {condition})"
    return result


def encode_query_param(value: str) -> str:
    """URL-encode a query parameter value.

    Args:
        value: The value to encode.

    Returns:
        URL-encoded string.
    """
    return quote(value, safe="")


def parse_query_result(data: dict[str, Any]) -> tuple[list[dict], int]:
    """Parse a Rally query response.

    Args:
        data: The JSON response data.

    Returns:
        Tuple of (results list, total count).

    Raises:
        RallyAPIError: If the response contains errors.
    """
    # Check for errors in QueryResult
    if "QueryResult" in data:
        result = data["QueryResult"]
        errors = result.get("Errors", [])
        if errors:
            raise RallyAPIError(
                message=errors[0],
                errors=errors,
                warnings=result.get("Warnings", []),
            )
        return result.get("Results", []), result.get("TotalResultCount", 0)

    # Check for errors in OperationResult (create/update)
    if "OperationResult" in data:
        result = data["OperationResult"]
        errors = result.get("Errors", [])
        if errors:
            raise RallyAPIError(
                message=errors[0],
                errors=errors,
                warnings=result.get("Warnings", []),
            )
        # Return the created/updated object
        obj = result.get("Object")
        if obj:
            return [obj], 1
        return [], 0

    # Check for create result
    if "CreateResult" in data:
        result = data["CreateResult"]
        errors = result.get("Errors", [])
        if errors:
            raise RallyAPIError(
                message=errors[0],
                errors=errors,
                warnings=result.get("Warnings", []),
            )
        obj = result.get("Object")
        if obj:
            return [obj], 1
        return [], 0

    return [], 0


def build_base_url(server: str) -> str:
    """Build the base URL for Rally WSAPI.

    Args:
        server: The Rally server hostname.

    Returns:
        The base URL for API requests.
    """
    # Ensure server doesn't have protocol prefix
    if server.startswith("https://"):
        server = server[8:]
    elif server.startswith("http://"):
        server = server[7:]

    return f"https://{server}/slm/webservice/{RALLY_WSAPI_VERSION}"
