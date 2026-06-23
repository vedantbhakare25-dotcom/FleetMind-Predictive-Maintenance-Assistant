# Reads rows sequentially from AI4I CSV, posts each row as a sensor reading to the FastAPI sensor ingestion endpoint at a configurable interval to simulate live machine sensor streams
# Sensor simulation script for FleetMind
# Pretends to be real IoT sensors sending live data
# Reads rows from AI4I dataset and posts them to the API continuously

import time
import random
import requests
import pandas as pd
from pathlib import Path


# ── Configuration ──────────────────────────────────────────────────────────────

API_BASE_URL = "http://127.0.0.1:8000"
AI4I_PATH = Path(__file__).parent.parent / "ml" / "data" / "raw" / "ai4i2020.csv"

# Login credentials for the simulator (uses Ramesh's account to authenticate)
LOGIN_EMAIL = "ramesh@fleetmind.dev"
LOGIN_PASSWORD = "FleetMind@123"

# How long to wait between sending readings (seconds)
INTERVAL_SECONDS = 5

# Your 5 machine UUIDs from Step 3 seed data
# Replace these with your actual machine UUIDs from Supabase
MACHINE_IDS = {
    "CNC Machine Alpha"      : "76c4506d-ee57-4eed-925e-c667a0439ca6",
    "CNC Machine Beta"       : "a26c6d41-0558-4bc6-ac83-80c456ba5a58",
    "Industrial Pump Gamma"  : "5cd93606-0f08-43be-8fbe-956b8c6fd067",  # from your test
    "Compressor Delta"       : "edf996e7-00a7-4b8b-814e-f488c172ddac",
    "Conveyor Motor Epsilon" : "8461656d-ac5e-4566-99ce-c236dc583c4e"
}


# ── Authentication ─────────────────────────────────────────────────────────────

def get_auth_token() -> str:
    """
    Logs in via Supabase REST API directly (no need for the Python SDK here)
    and returns a JWT access token to use for all subsequent requests.
    """
    import os
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_SERVICE_KEY")  # service key works for this too

    auth_url = f"{supabase_url}/auth/v1/token?grant_type=password"

    response = requests.post(
        auth_url,
        headers={
            "apikey": supabase_anon_key,
            "Content-Type": "application/json"
        },
        json={
            "email": LOGIN_EMAIL,
            "password": LOGIN_PASSWORD
        }
    )

    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")

    token = response.json()["access_token"]
    print("   Authenticated successfully\n")
    return token


# ── Data Loading ────────────────────────────────────────────────────────────────

def load_ai4i_rows() -> pd.DataFrame:
    """
    Loads the AI4I dataset and returns just the columns we need
    for simulating sensor readings.
    """
    df = pd.read_csv(AI4I_PATH)

    print(f"   Loaded {len(df)} rows from AI4I dataset")
    print(f"   Failure rows available: {df['Machine failure'].sum()}")
    print(f"   Normal rows available : {(df['Machine failure']==0).sum()}\n")

    return df


def row_to_reading(row: pd.Series, machine_id: str) -> dict:
    """
    Converts one AI4I dataframe row into the JSON shape
    expected by POST /api/sensors/readings.

    Reads FROM the raw CSV's original bracket-style column names,
    writes TO the clean snake_case names our API expects.
    """
    return {
        "machine_id"          : machine_id,
        "air_temperature"     : float(row["Air temperature [K]"]),
        "process_temperature" : float(row["Process temperature [K]"]),
        "rotational_speed"    : float(row["Rotational speed [rpm]"]),
        "torque"              : float(row["Torque [Nm]"]),
        "tool_wear"           : float(row["Tool wear [min]"])
    }


# ── Posting to API ─────────────────────────────────────────────────────────────

def post_reading(reading: dict, token: str) -> dict:
    """
    Sends one sensor reading to the FastAPI backend.
    """
    response = requests.post(
        f"{API_BASE_URL}/api/sensors/readings",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=reading
    )

    if response.status_code != 200:
        print(f"   ❌ Failed: {response.status_code} — {response.text}")
        return None

    return response.json()


def trigger_prediction(machine_id: str, token: str) -> dict:
    """
    Calls the prediction endpoint right after sending a reading,
    so you see the health score update immediately.
    """
    response = requests.post(
        f"{API_BASE_URL}/api/predictions/run/{machine_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"   ⚠️  Prediction failed: {response.status_code}")
        return None

    return response.json()


# ── Main Simulation Loop ────────────────────────────────────────────────────────

def run_simulation(mode: str = "sequential", num_readings: int = 20):
    """
    Runs the simulation loop.

    Args:
        mode: 'sequential' walks through AI4I rows in order (good for
              demoing a single machine gradually degrading)
              'random' picks random rows each time (good for stress
              testing multiple machines at once)
        num_readings: how many readings to send before stopping
    """

    print("=" * 60)
    print("FLEETMIND SENSOR SIMULATOR")
    print("=" * 60)

    token = get_auth_token()
    df = load_ai4i_rows()

    # Validate machine IDs are filled in
    if any(v.startswith("REPLACE") for v in MACHINE_IDS.values()):
        print("⚠️  WARNING: Some machine IDs are still placeholders.")
        print("   Update MACHINE_IDS at the top of this script.\n")

    valid_machines = [
        (name, mid) for name, mid in MACHINE_IDS.items()
        if not mid.startswith("REPLACE")
    ]

    if not valid_machines:
        print("❌ No valid machine IDs configured. Exiting.")
        return

    print(f"Simulating for {len(valid_machines)} machine(s): "
          f"{[name for name, _ in valid_machines]}")
    print(f"Mode: {mode} | Readings to send: {num_readings}")
    print(f"Interval: {INTERVAL_SECONDS}s between readings\n")
    print("-" * 60)

    row_index = 0

    for i in range(num_readings):

        # ── Pick a row ──────────────────────────────────────────────────────
        if mode == "sequential":
            row = df.iloc[row_index % len(df)]
            row_index += 1
        else:  # random
            row = df.sample(1).iloc[0]

        # ── Pick a machine ──────────────────────────────────────────────────
        machine_name, machine_id = random.choice(valid_machines)

        # ── Build and send reading ──────────────────────────────────────────
        reading = row_to_reading(row, machine_id)
        is_failure_row = row["Machine failure"] == 1

        status_tag = "⚠️  FAILURE-LIKE" if is_failure_row else "   normal"

        print(f"\n[{i+1}/{num_readings}] Sending to: {machine_name}  ({status_tag})")
        print(f"   temp={reading['process_temperature']:.1f}K  "
              f"rpm={reading['rotational_speed']:.0f}  "
              f"torque={reading['torque']:.1f}  "
              f"wear={reading['tool_wear']:.0f}")

        result = post_reading(reading, token)

        if result:
            print(f"      Reading stored")

            # Trigger a prediction right away to see live health updates
            prediction = trigger_prediction(machine_id, token)
            if prediction:
                health = prediction["health_score"]
                print(f"   📊 Health Score: {health['score']}/100 "
                      f"({health['level']})  "
                      f"Failure prob: {prediction['failure_probability']*100:.1f}%")

                if prediction.get("alert_created"):
                    print(f"   🚨 ALERT CREATED: {prediction['alert_level']}")

        time.sleep(INTERVAL_SECONDS)

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)


# ── Entry Point ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Sequential mode walks through AI4I rows in order
    # This naturally shows a mix of healthy and failing readings
    # since the dataset isn't sorted by failure status
    run_simulation(mode="sequential", num_readings=20)