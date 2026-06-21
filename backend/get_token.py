# Temporary script to get a JWT token for testing in Swagger UI
# DELETE this file before committing — never commit credentials

from supabase import create_client
from app.core.config import settings

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Sign in as Ramesh using the credentials you created in Step 3
response = supabase.auth.sign_in_with_password({
    "email": "ramesh@fleetmind.dev",
    "password": "FleetMind@123"
})

print("=" * 60)
print("ACCESS TOKEN (copy everything after 'Bearer ')")
print("=" * 60)
print(response.session.access_token)
print("=" * 60)
print(f"\nUser ID: {response.user.id}")
print(f"Email  : {response.user.email}")