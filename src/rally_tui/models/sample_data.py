"""Sample ticket data for development and testing."""

from datetime import datetime, timezone

from .discussion import Discussion
from .ticket import Ticket

SAMPLE_TICKETS: list[Ticket] = [
    Ticket(
        formatted_id="US1234",
        name="User login feature",
        ticket_type="UserStory",
        state="In-Progress",
        owner="John Smith",
        description="As a user, I want to log in with my email and password so that I can access my account securely.",
        notes="Technical notes: Use bcrypt for password hashing. Session tokens expire after 24 hours. Rate limit: 5 attempts per minute.",
        iteration="Sprint 5",
        points=3,
        object_id="100001",
    ),
    Ticket(
        formatted_id="US1235",
        name="Password reset functionality",
        ticket_type="UserStory",
        state="Defined",
        owner="Jane Doe",
        description="As a user, I want to reset my password via email so that I can regain access if I forget it.",
        notes="Implementation notes: Reset tokens valid for 1 hour. Send notification email when password is changed.",
        iteration="Sprint 6",
        points=5,
        object_id="100002",
    ),
    Ticket(
        formatted_id="DE456",
        name="Fix null pointer exception on checkout",
        ticket_type="Defect",
        state="Open",
        owner="Bob Wilson",
        description="NullPointerException thrown when user clicks checkout with an empty cart. Stack trace attached.",
        notes="Root cause: CartService.getTotal() doesn't handle null items array. Fix: Add null check before iteration.",
        iteration="Sprint 5",
        points=2,
        object_id="100003",
    ),
    Ticket(
        formatted_id="US1236",
        name="Add logout button to navbar",
        ticket_type="UserStory",
        state="Completed",
        owner="Alice Chen",
        description="Add a clearly visible logout button in the navigation bar for authenticated users.",
        notes="",
        iteration="Sprint 4",
        points=1,
        object_id="100004",
    ),
    Ticket(
        formatted_id="TA789",
        name="Write unit tests for auth module",
        ticket_type="Task",
        state="In-Progress",
        owner="John Smith",
        description="Create comprehensive unit tests for the authentication module including login, logout, and session management.",
        notes="Test coverage target: 80%. Include edge cases for invalid tokens and expired sessions.",
        iteration="Sprint 5",
        points=None,  # Tasks often don't have points
        object_id="100005",
    ),
    Ticket(
        formatted_id="DE457",
        name="Memory leak in image processing",
        ticket_type="Defect",
        state="Open",
        owner=None,  # Unassigned
        description="Memory usage grows unbounded when processing multiple images. Heap dump analysis needed.",
        notes="",
        iteration=None,  # Unscheduled
        points=None,
        object_id="100006",
    ),
    Ticket(
        formatted_id="TC101",
        name="Verify login with valid credentials",
        ticket_type="TestCase",
        state="Defined",
        owner="QA Team",
        description="Test that users can successfully log in with valid email/password combinations.",
        notes="Test data: Use test accounts from QA environment. Check session cookie is set correctly.",
        iteration="Sprint 5",
        points=None,
        object_id="100007",
    ),
    Ticket(
        formatted_id="US1237",
        name="Implement dark mode toggle",
        ticket_type="UserStory",
        state="Defined",
        owner=None,  # Unassigned
        description="Allow users to switch between light and dark themes via a toggle in settings.",
        notes="Design spec: Toggle should persist across sessions. Use CSS variables for theme colors.",
        iteration=None,  # Backlog
        points=8,
        object_id="100008",
    ),
]


SAMPLE_DISCUSSIONS: dict[str, list[Discussion]] = {
    "US1234": [
        Discussion(
            object_id="200001",
            text="I've started working on the login form. Will have a PR ready by end of day.",
            user="John Smith",
            created_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            artifact_id="US1234",
        ),
        Discussion(
            object_id="200002",
            text="Looks good! Don't forget to add input validation for the email field.",
            user="Jane Doe",
            created_at=datetime(2024, 1, 15, 14, 45, tzinfo=timezone.utc),
            artifact_id="US1234",
        ),
        Discussion(
            object_id="200003",
            text="Good point. I've added email format validation and password strength checks.",
            user="John Smith",
            created_at=datetime(2024, 1, 16, 9, 15, tzinfo=timezone.utc),
            artifact_id="US1234",
        ),
    ],
    "DE456": [
        Discussion(
            object_id="200004",
            text="I can reproduce this. It happens when the cart is empty and user clicks checkout.",
            user="Bob Wilson",
            created_at=datetime(2024, 1, 14, 11, 0, tzinfo=timezone.utc),
            artifact_id="DE456",
        ),
        Discussion(
            object_id="200005",
            text="The issue is in CartService.getTotal() - it doesn't check for null items array.",
            user="Bob Wilson",
            created_at=datetime(2024, 1, 14, 15, 30, tzinfo=timezone.utc),
            artifact_id="DE456",
        ),
    ],
    "US1236": [
        Discussion(
            object_id="200006",
            text="Completed the logout button. It's now visible in the top-right corner of the navbar.",
            user="Alice Chen",
            created_at=datetime(2024, 1, 10, 16, 0, tzinfo=timezone.utc),
            artifact_id="US1236",
        ),
    ],
}
