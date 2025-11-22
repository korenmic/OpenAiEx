"""Content moderation service."""
import re
from typing import List

from app.services.username_cache import UsernameCache


class ContentModerator:
    """Content moderation service for detecting username mentions."""

    def __init__(self, username_cache: UsernameCache):
        """Initialize content moderator."""
        self.username_cache = username_cache

    async def check_for_violations(self, message: str, requesting_username: str) -> List[str]:
        """
        Check for username mentions in message.

        Returns list of mentioned usernames found in message.
        Uses cached username list for efficiency.
        """
        # Get all usernames except the requesting user
        all_usernames = await self.username_cache.get_usernames_except(requesting_username)

        # Detect mentions using word boundary matching
        return self._detect_mentions(message, all_usernames, requesting_username)

    def _detect_mentions(
        self, message: str, all_usernames: set[str], requesting_user: str
    ) -> List[str]:
        """
        Detect username mentions in message using word boundary matching.
        Case-insensitive, exact word matches only.
        """
        # Tokenize into words (alphanumeric + underscore)
        words = re.findall(r"\b\w+\b", message.lower())

        # Check each word against usernames (case-insensitive)
        mentioned = []
        usernames_lower = {
            u.lower(): u for u in all_usernames if u.lower() != requesting_user.lower()
        }

        for word in words:
            if word in usernames_lower:
                mentioned.append(usernames_lower[word])

        return list(set(mentioned))  # Remove duplicates
