"""Owner-related utility functions."""

from rally_tui.models import Owner, Ticket


def extract_owners_from_tickets(tickets: list[Ticket]) -> set[Owner]:
    """Extract unique owners from a list of tickets as STUB objects.

    IMPORTANT: Returns Owner objects with display_name used as temporary object_id
    (prefixed with "TEMP:"). These MUST be enriched via get_users() API call to
    get real object IDs before caching or using in API operations.

    Args:
        tickets: List of tickets to extract owners from

    Returns:
        Set of STUB Owner objects requiring enrichment.
        Tickets with no owner (owner=None) are skipped.
    """
    owners: set[Owner] = set()
    for ticket in tickets:
        if ticket.owner:
            # Create stub Owner - MUST be enriched with get_users() before caching
            owner = Owner(
                object_id=f"TEMP:{ticket.owner}",  # Temporary ID, needs enrichment
                display_name=ticket.owner,
                user_name=None,
            )
            owners.add(owner)
    return owners
