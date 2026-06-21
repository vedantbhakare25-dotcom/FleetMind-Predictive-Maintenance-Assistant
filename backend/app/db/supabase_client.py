# Initializes and returns a singleton Supabase client using service role key, used by all services
# Singleton Supabase client for FleetMind backend
# Uses service_role key — bypasses RLS since backend enforces its own auth

from supabase import create_client, Client
from app.core.config import settings


_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Returns a singleton Supabase client.
    Creates the connection once on first call, reuses it after.
    """
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_KEY
        )

    return _supabase_client


# Convenience instance — imported directly by services
# e.g. from app.db.supabase_client import supabase
supabase = get_supabase_client()