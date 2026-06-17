#-----------------------------------------------------------------------------

# FastAPI dependency injection functions for FleetMind
# Provides reusable auth and role checking for all routes

from fastapi import HTTPException, status, Depends
from app.core.security import get_current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory for role-based access control.

    Usage in routes:
        # Only admins can access this route
        @router.post("/machines")
        async def create_machine(user = Depends(require_role("admin"))):
            ...

        # Engineers and managers can access this route
        @router.get("/machines")
        async def get_machines(user = Depends(require_role("engineer", "manager", "admin"))):
            ...

    Args:
        *allowed_roles: one or more role strings that can access the route

    Returns:
        A dependency function that FastAPI injects into the route
    """

    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        """
        Checks if the authenticated user has one of the allowed roles.
        FastAPI calls this automatically before the route function runs.
        """
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(allowed_roles)}. "
                       f"Your role: {user.get('role')}."
            )
        return user

    return role_checker


def require_plant(user: dict = Depends(get_current_user)) -> str:
    """
    Ensures the authenticated user belongs to a plant.
    Returns the plant_id for use in database queries.

    Raises 403 if user has no plant assigned.
    Admins without a plant assignment cannot query machine data.
    """
    plant_id = user.get("plant_id")

    if not plant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to any plant. "
                   "Contact administrator to assign a plant."
        )

    return plant_id


#Convenience aliases 
# Import these in routes for cleaner code

# Any authenticated user
any_authenticated = get_current_user

# Engineers, managers, and admins (most read operations)
engineer_or_above = require_role("engineer", "manager", "admin")

# Managers and admins only (analytics, reports)
manager_or_above = require_role("manager", "admin")

# Admins only (create/delete machines, manage users)
admin_only = require_role("admin")