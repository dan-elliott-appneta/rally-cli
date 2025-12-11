"""Sample ticket data for development and testing."""

from .ticket import Ticket

SAMPLE_TICKETS: list[Ticket] = [
    Ticket(
        formatted_id="US1234",
        name="User login feature",
        ticket_type="UserStory",
        state="In Progress",
        owner="John Smith",
        description="As a user, I want to log in with my email and password so that I can access my account securely.",
        iteration="Sprint 5",
        points=3,
    ),
    Ticket(
        formatted_id="US1235",
        name="Password reset functionality",
        ticket_type="UserStory",
        state="Defined",
        owner="Jane Doe",
        description="As a user, I want to reset my password via email so that I can regain access if I forget it.",
        iteration="Sprint 6",
        points=5,
    ),
    Ticket(
        formatted_id="DE456",
        name="Fix null pointer exception on checkout",
        ticket_type="Defect",
        state="Open",
        owner="Bob Wilson",
        description="NullPointerException thrown when user clicks checkout with an empty cart. Stack trace attached.",
        iteration="Sprint 5",
        points=2,
    ),
    Ticket(
        formatted_id="US1236",
        name="Add logout button to navbar",
        ticket_type="UserStory",
        state="Completed",
        owner="Alice Chen",
        description="Add a clearly visible logout button in the navigation bar for authenticated users.",
        iteration="Sprint 4",
        points=1,
    ),
    Ticket(
        formatted_id="TA789",
        name="Write unit tests for auth module",
        ticket_type="Task",
        state="In Progress",
        owner="John Smith",
        description="Create comprehensive unit tests for the authentication module including login, logout, and session management.",
        iteration="Sprint 5",
        points=None,  # Tasks often don't have points
    ),
    Ticket(
        formatted_id="DE457",
        name="Memory leak in image processing",
        ticket_type="Defect",
        state="Open",
        owner=None,  # Unassigned
        description="Memory usage grows unbounded when processing multiple images. Heap dump analysis needed.",
        iteration=None,  # Unscheduled
        points=None,
    ),
    Ticket(
        formatted_id="TC101",
        name="Verify login with valid credentials",
        ticket_type="TestCase",
        state="Defined",
        owner="QA Team",
        description="Test that users can successfully log in with valid email/password combinations.",
        iteration="Sprint 5",
        points=None,
    ),
    Ticket(
        formatted_id="US1237",
        name="Implement dark mode toggle",
        ticket_type="UserStory",
        state="Defined",
        owner=None,  # Unassigned
        description="Allow users to switch between light and dark themes via a toggle in settings.",
        iteration=None,  # Backlog
        points=8,
    ),
]
