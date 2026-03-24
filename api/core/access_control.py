"""Access control for copilot tools.

Provides SEHRA-level access checks that can be extended later
with country-level or role-based restrictions.
"""

import logging

logger = logging.getLogger("sehra.access_control")


def check_sehra_access(user: dict, sehra_id: str) -> bool:
    """Check if a user has access to a specific SEHRA assessment.

    Currently allows all authenticated users to access all SEHRAs.
    This function is the extension point for future access restrictions
    (e.g., country-level, organization-level, or role-based).

    Args:
        user: Dict with 'sub' (username), 'name', and 'role' from JWT.
        sehra_id: The SEHRA assessment ID to check access for.

    Returns:
        True if access is allowed, False otherwise.
    """
    username = user.get("sub", "unknown")
    role = user.get("role", "analyst")

    # Admins always have access
    if role == "admin":
        return True

    # --- Future extension point ---
    # Add country-level restrictions here:
    #   sehra = db.get_sehra(sehra_id)
    #   if sehra and sehra["country"] not in get_user_countries(username):
    #       logger.warning(
    #           "Access denied: user=%s has no access to country=%s (sehra=%s)",
    #           username, sehra["country"], sehra_id,
    #       )
    #       return False

    # For now, all authenticated users can access all SEHRAs
    return True


def verify_tool_access(user: dict, tool_name: str, args: dict) -> bool:
    """Verify that a user can execute a specific copilot tool with the given args.

    Checks SEHRA access for any tool that operates on a sehra_id.

    Args:
        user: Dict with 'sub' (username), 'name', and 'role' from JWT.
        tool_name: The copilot tool name being executed.
        args: The arguments being passed to the tool.

    Returns:
        True if access is allowed, False otherwise.
    """
    username = user.get("sub", "unknown")

    # Extract sehra_id from various argument patterns
    sehra_id = args.get("sehra_id") or args.get("sehra_id_a")
    sehra_id_b = args.get("sehra_id_b")

    if sehra_id and not check_sehra_access(user, sehra_id):
        logger.warning(
            "Access denied: user=%s tool=%s sehra_id=%s",
            username, tool_name, sehra_id,
        )
        return False

    if sehra_id_b and not check_sehra_access(user, sehra_id_b):
        logger.warning(
            "Access denied: user=%s tool=%s sehra_id_b=%s",
            username, tool_name, sehra_id_b,
        )
        return False

    return True
