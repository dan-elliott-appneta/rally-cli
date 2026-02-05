"""Owner-related utility functions."""

from rally_tui.models import Owner, Ticket


def extract_owners_from_tickets(tickets: list[Ticket]) -> set[Owner]:
    """Extract unique owners from a list of tickets.

    Args:
        tickets: List of tickets to extract owners from

    Returns:
        Set of Owner objects representing unique owners.
        Tickets with no owner (owner=None) are skipped.
    """
    owners: set[Owner] = set()
    for ticket in tickets:
        if ticket.owner:
            # Create Owner with display_name from ticket.owner field
            # Note: We don't have object_id or user_name from ticket data,
            # so we'll need to use display_name as a temporary identifier
            # The full Owner object will be populated when get_users() is called
            owner = Owner(
                object_id=ticket.owner,  # Use display_name as temp ID
                display_name=ticket.owner,
                user_name=None,
            )
            owners.add(owner)
    return owners
