"""Sample ticket data for development and testing."""

from .ticket import Ticket

SAMPLE_TICKETS: list[Ticket] = [
    Ticket(
        formatted_id="US1234",
        name="User login feature",
        ticket_type="UserStory",
        state="In Progress",
        owner="John Smith",
    ),
    Ticket(
        formatted_id="US1235",
        name="Password reset functionality",
        ticket_type="UserStory",
        state="Defined",
        owner="Jane Doe",
    ),
    Ticket(
        formatted_id="DE456",
        name="Fix null pointer exception on checkout",
        ticket_type="Defect",
        state="Open",
        owner="Bob Wilson",
    ),
    Ticket(
        formatted_id="US1236",
        name="Add logout button to navbar",
        ticket_type="UserStory",
        state="Completed",
        owner="Alice Chen",
    ),
    Ticket(
        formatted_id="TA789",
        name="Write unit tests for auth module",
        ticket_type="Task",
        state="In Progress",
        owner="John Smith",
    ),
    Ticket(
        formatted_id="DE457",
        name="Memory leak in image processing",
        ticket_type="Defect",
        state="Open",
        owner=None,
    ),
    Ticket(
        formatted_id="TC101",
        name="Verify login with valid credentials",
        ticket_type="TestCase",
        state="Defined",
        owner="QA Team",
    ),
    Ticket(
        formatted_id="US1237",
        name="Implement dark mode toggle",
        ticket_type="UserStory",
        state="Defined",
        owner=None,
    ),
]
