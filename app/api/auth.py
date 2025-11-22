"""Admin authentication."""
from fastapi import Header, HTTPException, status


async def verify_admin_key(x_admin_key: str = Header(...)) -> str:
    """Verify admin API key from header."""
    from app.core.config import get_settings

    settings = get_settings()
    admin_key = settings.get_or_generate_admin_key()

    if x_admin_key != admin_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin API key"
        )

    return x_admin_key
