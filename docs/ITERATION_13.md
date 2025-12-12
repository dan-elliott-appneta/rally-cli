# Iteration 13: Attachments

## Goal

Enable users to view, download, and upload attachments on Rally tickets directly from the TUI.

## Overview

Attachments are files associated with Rally artifacts (User Stories, Defects, etc.). This iteration adds full attachment support:

- **View**: See list of attachments on a ticket with name, size, and type
- **Download**: Save attachments to local filesystem
- **Upload**: Add new attachments from local files

## Rally API Reference

The `pyral` library provides these attachment methods:

```python
# Get all attachments for an artifact
attachments = rally.getAttachments(artifact)

# Get specific attachment by name
attachment = rally.getAttachment(artifact, 'filename.pdf')

# Get attachment names only
names = rally.getAttachmentNames(artifact)

# Add attachment (max 50MB)
rally.addAttachment(artifact, '/path/to/file.pdf', mime_type='application/pdf')
```

Attachment objects have these properties:
- `Name` - filename
- `Size` - size in bytes
- `ContentType` - MIME type (e.g., 'application/pdf')
- `Content` - base64 encoded content (when fetched)
- `ObjectID` - unique identifier

## UI Design

### Attachments Screen

Press `a` on a ticket to open the AttachmentsScreen modal:

```
┌─────────────────────────────────────────────────────────────┐
│ Attachments - US1234                                    [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. requirements.pdf              245 KB    application/pdf │
│  2. screenshot.png                 89 KB    image/png       │
│  3. test-data.csv                  12 KB    text/csv        │
│                                                             │
│  ───────────────────────────────────────────────────────── │
│  [1-9] Download  [u] Upload  [Esc] Close                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Empty State

```
┌─────────────────────────────────────────────────────────────┐
│ Attachments - US1234                                    [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              No attachments on this ticket.                 │
│                                                             │
│  ───────────────────────────────────────────────────────── │
│  [u] Upload  [Esc] Close                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Upload Dialog

Press `u` to open upload input:

```
┌─────────────────────────────────────────────────────────────┐
│ Upload Attachment - US1234                              [X] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Enter file path:                                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ /home/user/documents/report.pdf                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Enter] Upload  [Esc] Cancel                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Ticket Detail Enhancement

Show attachment count in the detail panel:

```
State: In-Progress
Owner: John Smith
Iteration: Sprint 5
Points: 3
Attachments: 3 files
```

## Data Model

### Attachment Dataclass

```python
@dataclass(frozen=True)
class Attachment:
    """Represents a file attachment on a Rally artifact."""

    name: str
    size: int  # bytes
    content_type: str
    object_id: str

    @property
    def formatted_size(self) -> str:
        """Human-readable file size."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size // 1024} KB"
        else:
            return f"{self.size // (1024 * 1024):.1f} MB"

    @property
    def short_type(self) -> str:
        """Short content type display."""
        # application/pdf -> pdf
        # image/png -> png
        return self.content_type.split('/')[-1] if '/' in self.content_type else self.content_type
```

## Protocol Updates

Add to `RallyClientProtocol`:

```python
def get_attachments(self, ticket: Ticket) -> list[Attachment]:
    """Get all attachments for a ticket."""
    ...

def download_attachment(self, ticket: Ticket, attachment: Attachment, dest_path: str) -> bool:
    """Download attachment content to local file. Returns True on success."""
    ...

def upload_attachment(self, ticket: Ticket, file_path: str) -> Attachment | None:
    """Upload a local file as attachment. Returns the created Attachment or None on failure."""
    ...
```

## Implementation Tasks

### 1. Create Attachment Model
- [x] Create `src/rally_tui/models/attachment.py`
- [x] Add `Attachment` dataclass with name, size, content_type, object_id
- [x] Add `formatted_size` property for human-readable sizes
- [x] Add `short_type` property for display
- [x] Export from `models/__init__.py`
- [x] Write unit tests

### 2. Update Protocol
- [x] Add `get_attachments()` to `RallyClientProtocol`
- [x] Add `download_attachment()` to `RallyClientProtocol`
- [x] Add `upload_attachment()` to `RallyClientProtocol`

### 3. Implement MockRallyClient
- [x] Add `SAMPLE_ATTACHMENTS` dictionary (ticket_id -> list of attachments)
- [x] Implement `get_attachments()` returning mock data
- [x] Implement `download_attachment()` (simulated success)
- [x] Implement `upload_attachment()` (add to mock data)
- [x] Write service tests

### 4. Implement RallyClient
- [x] Implement `get_attachments()` using `rally.getAttachments()`
- [x] Implement `download_attachment()` using `rally.getAttachment()` and writing content
- [x] Implement `upload_attachment()` using `rally.addAttachment()`
- [x] Handle errors gracefully
- [x] Write tests with mocked pyral

### 5. Create AttachmentsScreen
- [x] Create `src/rally_tui/screens/attachments_screen.py`
- [x] Create `AttachmentItem` widget for list items
- [x] Implement number key shortcuts (1-9) for download
- [x] Implement `u` key for upload mode
- [x] Handle empty state gracefully
- [x] Add escape to close
- [x] Export from `screens/__init__.py`
- [x] Write screen tests

### 6. Create UploadScreen
- [x] Create upload input modal (or mode within AttachmentsScreen)
- [x] Path input with validation
- [x] File existence check
- [x] Size limit warning (50MB)
- [x] Success/error feedback

### 7. Integrate into App
- [x] Add `a` keybinding to open AttachmentsScreen
- [x] Add `action.attachments` to keybindings registry
- [x] Handle `AttachmentsScreen.Selected` message for downloads
- [x] Handle upload completion and refresh
- [x] Show notification on download/upload success

### 8. Update TicketDetail
- [x] Fetch attachment count when displaying ticket
- [x] Show "Attachments: N files" in detail panel
- [x] Update on ticket change

### 9. Documentation
- [x] Update README.md with attachment feature
- [x] Update PLAN.md to mark Iteration 13 complete
- [x] Update keybinding documentation

## Key Bindings

| Key | Context | Action |
|-----|---------|--------|
| `a` | list/detail | Open attachments screen |
| `1-9` | attachments | Download attachment by number |
| `u` | attachments | Upload new attachment |
| `Enter` | upload input | Confirm upload |
| `Esc` | attachments/upload | Close/cancel |

## Test Coverage

### Unit Tests
- Attachment model properties (formatted_size, short_type)
- Attachment equality and immutability
- Protocol method signatures

### Service Tests
- MockRallyClient.get_attachments() returns attachments
- MockRallyClient.download_attachment() simulates download
- MockRallyClient.upload_attachment() adds attachment
- RallyClient attachment method mapping (mocked pyral)

### Screen Tests
- AttachmentsScreen renders attachment list
- AttachmentsScreen handles empty state
- Number keys trigger download
- Upload mode activation
- Path validation
- Escape closes screen

### Integration Tests
- Press `a` opens attachments screen
- Download flow completes
- Upload flow completes
- Ticket detail shows attachment count

## Error Handling

1. **File not found**: Show error when upload path doesn't exist
2. **File too large**: Warn if file > 50MB before upload
3. **Network errors**: Show notification on API failures
4. **Permission errors**: Handle download directory not writable
5. **Invalid ticket**: Handle ticket without object_id

## Notes

- Downloads go to current working directory by default
- Upload accepts absolute or relative paths
- MIME type is auto-detected from file extension
- Maximum attachment size is 50MB (Rally limit)
- Attachment content is base64 encoded in the API

## Commit Plan

1. `feat: add Attachment model` - dataclass with properties
2. `feat: add attachment methods to protocol` - interface updates
3. `feat: implement MockRallyClient attachments` - mock implementation
4. `feat: implement RallyClient attachments` - real API calls
5. `feat: create AttachmentsScreen` - modal UI
6. `feat: add upload functionality` - file upload support
7. `feat: integrate attachments into app` - keybinding and flow
8. `feat: show attachment count in detail` - UI enhancement
9. `docs: update documentation for Iteration 13`
10. `chore: bump version to 0.7.0`
