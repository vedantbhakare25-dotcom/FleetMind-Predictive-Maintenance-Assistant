"""
Every protected API request passes through here first. 
It extracts the JWT token from the request header, sends it to Supabase to verify it's real and not expired, 
and returns the authenticated user's data. 

"""

# JWT validation middleware for FleetMind
# Verifies Supabase JWT tokens on every protected request

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.supabase_client import supabase


# HTTPBearer automatically extracts the Bearer token from
# the Authorization header on every request
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    Validates JWT token and returns the authenticated user's profile.

    This function is used as a FastAPI dependency — injected into
    every protected route via Depends(get_current_user).

    Flow:
        1. HTTPBearer extracts token from Authorization header
        2. We send token to Supabase Auth to verify
        3. We fetch the user's profile from our profiles table
        4. We return the profile dict to the calling route

    Raises:
        401 — if token is missing, invalid, or expired
        404 — if user profile not found in profiles table

    Returns:
        dict: {
            'id': 'uuid',
            'full_name': 'Ramesh Kumar',
            'role': 'engineer',
            'plant_id': 'uuid'
        }
    """

    token = credentials.credentials

    # ── Step 1: Verify token with Supabase Auth ────────────────────────────
    # Supabase checks: is this token real? is it expired? was it tampered?
    try:
        auth_response = supabase.auth.get_user(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not auth_response or not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = auth_response.user.id

    # ── Step 2: Fetch profile from our profiles table ──────────────────────
    # Supabase Auth only gives us id and email
    # Our profiles table has role and plant_id which we need for authorization
    try:
        profile_response = supabase.table("profiles") \
            .select("id, full_name, role, plant_id") \
            .eq("id", user_id) \
            .single() \
            .execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile not found. Please contact administrator."
        )

    if not profile_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found."
        )

    return profile_response.data


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)
    )
) -> dict | None:
    """
    Same as get_current_user but doesn't raise if token is missing.
    Used for endpoints that work both authenticated and unauthenticated.
    Currently unused in V1 but useful for public health check endpoints.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None