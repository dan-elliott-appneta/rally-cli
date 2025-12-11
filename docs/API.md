# Rally Web Services API (WSAPI) - Python Developer Guide

This document provides a comprehensive guide to using the Rally Web Services API (WSAPI) v2.0 with Python using the `pyral` toolkit.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Authentication](#authentication)
4. [The Rally Class](#the-rally-class)
5. [CRUD Operations](#crud-operations)
6. [Query Syntax](#query-syntax)
7. [Entity Types](#entity-types)
8. [Working with Collections](#working-with-collections)
9. [Attachments](#attachments)
10. [Error Handling](#error-handling)
11. [Rate Limits](#rate-limits)
12. [Best Practices](#best-practices)
13. [API Reference](#api-reference)

---

## Overview

Rally's Web Services API (WSAPI) v2.0 is a REST-based API that uses JSON for data exchange. The `pyral` package is the official Python toolkit for interacting with Rally.

**Key Characteristics:**
- REST architecture over HTTPS
- JSON request/response format
- Operates on one object at a time (no native batch operations, though pyral provides experimental batch methods)
- Referenced objects must exist before being referenced

**Base URL Pattern:**
```
https://rally1.rallydev.com/slm/webservice/v2.0/[resource]
```

---

## Installation

### Via pip (Recommended)

```bash
pip install pyral
```

### From Source

```bash
git clone https://github.com/RallyTools/RallyRestToolkitForPython.git
cd RallyRestToolkitForPython
python setup.py install
```

**Requirements:**
- Python 3.12, 3.13, or 3.14
- `requests` package (2.31.x or better; 2.32.5+ recommended)

---

## Authentication

### API Key (Recommended)

API Keys are the preferred authentication method. Obtain one from Rally Application Manager at `https://rally1.rallydev.com/login` under API Keys.

```python
from pyral import Rally

rally = Rally('rally1.rallydev.com', apikey='_your_api_key_here')
```

### Username/Password

```python
from pyral import Rally

rally = Rally('rally1.rallydev.com', user='[email protected]', password='your_password')
```

**Note:** If an API Key is provided, username and password are ignored.

### Configuration File

Create a config file (e.g., `rally_config.cfg`):

```ini
SERVER   = rally1.rallydev.com
APIKEY   = _your_api_key_here
WORKSPACE = My Workspace
PROJECT   = My Project
```

Then use `rallyWorkset()`:

```python
import sys
from pyral import Rally, rallyWorkset

options = [arg for arg in sys.argv[1:] if arg.startswith('--')]
server, user, password, apikey, workspace, project = rallyWorkset(options)
rally = Rally(server, user, password, apikey=apikey, workspace=workspace, project=project)
```

Run with: `python script.py --rallyConfig=rally_config.cfg`

### Command-Line Options

| Option | Description |
|--------|-------------|
| `--rallyConfig=<file>` | Configuration file path |
| `--rallyUser=<username>` | Rally username |
| `--rallyPassword=<pwd>` | User password |
| `--apikey=<key>` | API Key value |
| `--rallyWorkspace=<name>` | Workspace name |
| `--rallyProject=<name>` | Project name |

---

## The Rally Class

### Constructor

```python
Rally(server, user=None, password=None, apikey=None, workspace=None,
      project=None, warn=True, verify_ssl_cert=True, isolated_workspace=False,
      headers=None)
```

**Parameters:**
| Parameter | Description |
|-----------|-------------|
| `server` | Rally server hostname (e.g., `rally1.rallydev.com`) |
| `user` | Username for authentication |
| `password` | Password for authentication |
| `apikey` | API Key (alternative to user/password) |
| `workspace` | Target workspace name |
| `project` | Target project name |
| `warn` | Enable/disable warnings (default: True) |
| `verify_ssl_cert` | Verify SSL certificates (default: True) |
| `isolated_workspace` | Performance optimization for single workspace (default: False) |
| `headers` | Custom HTTP headers |

### Workspace and Project Methods

```python
# Get/Set current workspace
rally.setWorkspace('My Workspace')
workspace = rally.getWorkspace()

# Get all accessible workspaces
workspaces = rally.getWorkspaces()
for wksp in workspaces:
    print(wksp.oid, wksp.Name)

# Get/Set current project
rally.setProject('My Project')
project = rally.getProject()

# Get all projects in a workspace
projects = rally.getProjects(workspace='My Workspace')
for proj in projects:
    print(proj.oid, proj.Name)
```

---

## CRUD Operations

### Create (put/create)

```python
# Create a Defect
defect_data = {
    "Project": rally.getProject().ref,
    "Name": "Login button not working",
    "Severity": "Major Problem",
    "Priority": "High",
    "State": "Open",
    "Description": "Users cannot click the login button on Chrome"
}
defect = rally.create('Defect', defect_data)
print(f"Created: {defect.FormattedID}")
```

```python
# Create a User Story
story_data = {
    "Project": rally.getProject().ref,
    "Name": "As a user, I want to reset my password",
    "Description": "Password reset functionality",
    "ScheduleState": "Defined"
}
story = rally.create('HierarchicalRequirement', story_data)
print(f"Created: {story.FormattedID}")
```

### Read (get/find)

```python
# Query all defects
response = rally.get('Defect', fetch=True)
for defect in response:
    print(f"{defect.FormattedID}: {defect.Name}")

# Query with specific fields
response = rally.get('Defect', fetch="FormattedID,Name,Severity,State")

# Query with criteria
response = rally.get('Defect',
                     fetch="FormattedID,Name,Severity",
                     query='(Severity = "Major Problem")')

# Get by FormattedID
response = rally.get('Defect',
                     fetch=True,
                     query='FormattedID = "DE1234"')
defect = response.next()
```

**get() Parameters:**

| Parameter | Description |
|-----------|-------------|
| `entityName` | Type of entity (e.g., 'Defect', 'HierarchicalRequirement') |
| `fetch` | Fields to retrieve: `True` (all), `False` (minimal), or comma-separated string |
| `query` | Query string for filtering |
| `order` | Sort order (e.g., `"Name"`, `"CreationDate desc"`) |
| `pagesize` | Results per page (default: 500, max: 2000) |
| `start` | Starting index (1-based) |
| `limit` | Maximum total results |
| `workspace` | Override workspace |
| `project` | Override project |
| `projectScopeUp` | Include parent projects (True/False) |
| `projectScopeDown` | Include child projects (True/False) |
| `threads` | Multi-threading for large results |

### Update (post/update)

```python
# Update by FormattedID
update_data = {
    "FormattedID": "DE1234",
    "State": "Fixed",
    "Notes": "Fixed in build 2.3.1"
}
defect = rally.update('Defect', update_data)

# Update by ObjectID
update_data = {
    "ObjectID": 123456789,
    "Priority": "Critical"
}
defect = rally.update('Defect', update_data)
```

### Delete

```python
# Delete by FormattedID
success = rally.delete('Defect', 'DE1234')

# Delete by ObjectID
success = rally.delete('Defect', 123456789)
```

---

## Query Syntax

### Basic Structure

Queries follow the pattern: `(FieldName operator "value")`

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `(State = "Open")` |
| `!=` | Not equals | `(State != "Closed")` |
| `<` | Less than | `(Priority < "High")` |
| `>` | Greater than | `(CreationDate > "2024-01-01")` |
| `<=` | Less than or equal | `(StoryPoints <= 5)` |
| `>=` | Greater than or equal | `(StoryPoints >= 3)` |
| `contains` | Substring match | `(Name contains "login")` |
| `!contains` | Does not contain | `(Name !contains "test")` |
| `in` | In set | `(Severity in "High,Critical")` |
| `!in` | Not in set | `(State !in "Closed,Resolved")` |
| `between` | In range | `(CreationDate between 2024-01-01 and 2024-12-31)` |
| `!between` | Not in range | `(Priority !between "Low" and "Medium")` |

### Combining Conditions

Use `AND` and `OR` with parentheses:

```python
# AND example
query = '((State = "Open") AND (Severity = "Major Problem"))'

# OR example
query = '((Priority = "High") OR (Priority = "Critical"))'

# Complex example
query = '(((State = "Open") AND (Severity = "Major Problem")) OR (Priority = "Critical"))'
```

### Querying Related Objects

Use dot notation for nested attributes:

```python
# Query by owner's username
query = '(Owner.UserName = "[email protected]")'

# Query by iteration name
query = '(Iteration.Name = "Sprint 5")'

# Query by project
query = '(Project.Name = "My Project")'
```

### Null Values

```python
# Find items with no owner
query = '(Owner = null)'

# Find items with an owner
query = '(Owner != null)'
```

### Sorting Results

```python
# Sort ascending
response = rally.get('Defect', fetch=True, order="Name")

# Sort descending
response = rally.get('Defect', fetch=True, order="CreationDate desc")

# Multiple sort fields
response = rally.get('Defect', fetch=True, order="Priority,CreationDate desc")
```

### Query Rules

1. **Parentheses required**: Every condition must be wrapped in parentheses
2. **Strings with spaces**: Must use double quotes: `(Name = "My Story")`
3. **Case sensitivity**: Field values are case-sensitive
4. **Date format**: Use ISO-8601: `YYYY-MM-DD` or `YYYY-MM-DDThh:mm:ssZ`

---

## Entity Types

### Artifact Types (Work Items)

| API Name | Description |
|----------|-------------|
| `HierarchicalRequirement` | User Story |
| `Defect` | Bug/Defect |
| `Task` | Task |
| `TestCase` | Test Case |
| `TestSet` | Test Set |
| `DefectSuite` | Defect Suite |

**Note:** User Stories are called `HierarchicalRequirement` in the API.

### Portfolio Items

Use slash notation for portfolio item types:

```python
# Get Features
response = rally.get('PortfolioItem/Feature', fetch=True)

# Get Initiatives
response = rally.get('PortfolioItem/Initiative', fetch=True)
```

### Other Common Types

| Type | Description |
|------|-------------|
| `Workspace` | Workspace |
| `Project` | Project |
| `Release` | Release |
| `Iteration` | Iteration/Sprint |
| `User` | User |
| `Tag` | Tag |
| `Attachment` | Attachment |
| `TestCaseResult` | Test result |
| `TestFolder` | Test folder |

### Type Inheritance

Rally types follow an inheritance hierarchy:

```
PersistableObject
└── DomainObject
    └── WorkspaceDomainObject
        └── Artifact
            └── RankableArtifact
                └── SchedulableArtifact
                    └── Defect, HierarchicalRequirement, etc.
```

Child types inherit all fields from parent types.

### Custom Fields

Custom fields are prefixed with `c_` in the API:

```python
# Query using custom field
query = '(c_CustomFieldName = "value")'

# Access custom field on object (pyral allows without c_ prefix)
print(defect.CustomFieldName)
# or
print(defect.c_CustomFieldName)
```

### Getting Available Fields

```python
# Get type definition
typedef = rally.typedef('Defect')

# Get allowed values for a field
allowed = rally.getAllowedValues('Defect', 'State')
for val in allowed:
    print(val.Name)

# Get states for an entity
states = rally.getStates('Defect')
```

---

## Working with Collections

### Accessing Collection Items

Collections (like Tasks on a Story) are accessed via iteration:

```python
response = rally.get('HierarchicalRequirement',
                     fetch="FormattedID,Name,Tasks",
                     query='FormattedID = "US1234"')
story = response.next()

# Iterate through tasks
for task in story.Tasks:
    print(f"  {task.FormattedID}: {task.Name}")
```

### Adding Items to Collections

```python
# Add tags to a defect
tags = [rally.get('Tag', query='Name = "urgent"').next()]
rally.addCollectionItems(defect, 'Tags', tags)
```

### Removing Items from Collections

```python
# Remove tags from a defect
rally.dropCollectionItems(defect, 'Tags', tags)
```

---

## Attachments

### Add Attachment

```python
# Add single attachment
rally.addAttachment(artifact, '/path/to/file.pdf', mime_type='application/pdf')

# Add multiple attachments
attachments = [
    {'name': 'file1.txt', 'content': 'text content'},
    {'name': 'file2.pdf', 'path': '/path/to/file2.pdf'}
]
rally.addAttachments(artifact, attachments)
```

**Note:** Maximum attachment size is 50MB.

### Get Attachments

```python
# Get attachment names
names = rally.getAttachmentNames(artifact)

# Get specific attachment
attachment = rally.getAttachment(artifact, 'filename.pdf')

# Get all attachments
attachments = rally.getAttachments(artifact)
```

---

## Error Handling

### Response Structure

Rally API responses include `Errors` and `Warnings` arrays:

```python
response = rally.get('Defect', fetch=True, query='(InvalidField = "x")')

# Check for errors
if response.errors:
    for error in response.errors:
        print(f"Error: {error}")

# Check for warnings
if response.warnings:
    for warning in response.warnings:
        print(f"Warning: {warning}")
```

### RallyRESTResponse Attributes

| Attribute | Description |
|-----------|-------------|
| `status_code` | HTTP status code |
| `errors` | List of error messages |
| `warnings` | List of warning messages |
| `resultCount` | Number of results |
| `startIndex` | Starting index |
| `pageSize` | Page size |

### Common HTTP Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - invalid credentials |
| 403 | Forbidden - insufficient permissions |
| 404 | Not Found - invalid endpoint or entity |
| 407 | Proxy Authentication Required |
| 408 | Request Timeout |
| 429 | Too Many Requests |
| 502 | Bad Gateway |
| 504 | Gateway Timeout |

### Exception Handling

```python
from pyral import Rally
from pyral.context import RallyRESTAPIError

try:
    rally = Rally('rally1.rallydev.com', apikey='invalid_key')
    response = rally.get('Defect')
except RallyRESTAPIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Rate Limits

Rally does not impose hourly or daily API call limits. However:

| Limit Type | Value |
|------------|-------|
| Concurrent requests per user | 12 max |
| Page size (v2.0) | 2000 max |
| Page size (v1.x) | 200 max |
| Attachment size | 50MB max |

**Important:** Exceeding 12 concurrent requests results in throttling. Rally may disable accounts causing server issues.

### Recommendations

1. Implement retry logic with exponential backoff
2. Respect `Retry-After` headers on 429 responses
3. Use appropriate page sizes (500 is default, 2000 max)
4. Avoid unnecessary concurrent requests

---

## Best Practices

### Performance

1. **Fetch only needed fields**: Specify exact fields instead of `fetch=True`
   ```python
   # Good
   response = rally.get('Defect', fetch="FormattedID,Name,State")

   # Less efficient
   response = rally.get('Defect', fetch=True)
   ```

2. **Use `isolated_workspace=True`** for single-workspace scripts:
   ```python
   rally = Rally(server, apikey=apikey, isolated_workspace=True)
   ```

3. **Use threading for large result sets**:
   ```python
   response = rally.get('Defect', fetch=True, threads=4)
   ```

4. **Limit results when possible**:
   ```python
   response = rally.get('Defect', fetch=True, limit=100)
   ```

### Reliability

1. **Implement retry logic**:
   ```python
   import time

   def get_with_retry(rally, entity, max_retries=3, **kwargs):
       for attempt in range(max_retries):
           try:
               return rally.get(entity, **kwargs)
           except Exception as e:
               if attempt < max_retries - 1:
                   time.sleep(2 ** attempt)  # Exponential backoff
               else:
                   raise
   ```

2. **Always check for errors**:
   ```python
   response = rally.get('Defect', fetch=True)
   if response.errors:
       raise Exception(f"Rally errors: {response.errors}")
   ```

3. **Validate before create/update**:
   ```python
   # Get allowed values first
   allowed_states = [s.Name for s in rally.getAllowedValues('Defect', 'State')]
   if new_state not in allowed_states:
       raise ValueError(f"Invalid state: {new_state}")
   ```

### Security

1. **Use API Keys** instead of passwords
2. **Store credentials securely** (environment variables or encrypted config)
3. **Use `verify_ssl_cert=True`** (default) in production

---

## API Reference

### Rally Class Methods

| Method | Description |
|--------|-------------|
| `get(entity, fetch, query, order, **kwargs)` | Query entities |
| `create(entity, data)` | Create entity |
| `update(entity, data)` | Update entity |
| `delete(entity, ident)` | Delete entity |
| `getWorkspace()` | Get current workspace |
| `setWorkspace(name)` | Set current workspace |
| `getWorkspaces()` | Get all workspaces |
| `getProject(name=None)` | Get project |
| `setProject(name)` | Set current project |
| `getProjects(workspace=None)` | Get all projects |
| `getUserInfo(oid, username, name)` | Get user info |
| `getAllUsers(workspace)` | Get all users |
| `typedef(entity)` | Get type definition |
| `getAllowedValues(entity, attr)` | Get allowed field values |
| `getStates(entity)` | Get entity states |
| `addAttachment(artifact, filename, mime_type)` | Add attachment |
| `getAttachment(artifact, filename)` | Get attachment |
| `getAttachments(artifact)` | Get all attachments |
| `addCollectionItems(item, collection, items)` | Add to collection |
| `dropCollectionItems(item, collection, items)` | Remove from collection |
| `enableLogging(dest, attrget, append)` | Enable debug logging |
| `disableLogging()` | Disable logging |

### Batch Operations (Experimental)

| Method | Description |
|--------|-------------|
| `createMultiple(entity, items, fields)` | Batch create |
| `updateMultiple(entity, items, fields)` | Batch update |

### Ranking Methods

| Method | Description |
|--------|-------------|
| `rankAbove(item, relative_to)` | Rank item above another |
| `rankBelow(item, relative_to)` | Rank item below another |
| `rankTop(item)` | Rank item to top |
| `rankBottom(item)` | Rank item to bottom |

---

## Quick Reference Examples

### Complete Working Script

```python
#!/usr/bin/env python3
"""Example Rally API script demonstrating common operations."""

from pyral import Rally, rallyWorkset
import sys

def main():
    # Setup from config or command line
    options = [arg for arg in sys.argv[1:] if arg.startswith('--')]
    server, user, password, apikey, workspace, project = rallyWorkset(options)

    # Connect to Rally
    rally = Rally(server, apikey=apikey, workspace=workspace, project=project)

    # Query open defects
    response = rally.get('Defect',
                         fetch="FormattedID,Name,State,Severity,Owner",
                         query='(State = "Open")',
                         order="Severity")

    print(f"Found {response.resultCount} open defects:\n")

    for defect in response:
        owner = defect.Owner.Name if defect.Owner else "Unassigned"
        print(f"{defect.FormattedID}: {defect.Name}")
        print(f"  Severity: {defect.Severity}, Owner: {owner}\n")

if __name__ == '__main__':
    main()
```

### Environment Variable Setup

```bash
export RALLY_SERVER=rally1.rallydev.com
export RALLY_APIKEY=_your_api_key
export RALLY_WORKSPACE="My Workspace"
export RALLY_PROJECT="My Project"
```

---

## Resources

- **Official Documentation**: https://pyral.readthedocs.io/
- **GitHub Repository**: https://github.com/RallyTools/RallyRestToolkitForPython
- **Example Scripts**: https://github.com/RallyCommunity/rally-python-api-examples
- **Rally TechDocs**: https://techdocs.broadcom.com/us/en/ca-enterprise-software/valueops/rally/rally-help/reference/rally-web-services-api.html
