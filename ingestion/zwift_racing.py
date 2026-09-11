import httpx
import os
import json

BASE_URL = "https://api.zwiftracing.app/api/public/"
HEADER = {"Authorization": os.getenv("ZWIFT_RACING_API_KEY")}


def get_rider(rider_id: int, use_json=False):
    if use_json:
        with open("data/raw/rider.json", "r") as f:
            # indexing used because of yield behaviour; without it becomes a list of list of dicts
            rider = json.load(f)[0]
    else:
        response = httpx.get(f"{BASE_URL}riders/{rider_id}", headers=HEADER)
        response.raise_for_status()
        rider = response.json()

    yield rider


def get_riders(rider_ids: list[int], use_json=False):
    if use_json:
        with open("data/raw/riders.json", "r") as f:
            riders = json.load(f)
    else:
        response = httpx.post(f"{BASE_URL}riders/", headers=HEADER, json=rider_ids)
        response.raise_for_status()
        riders = response.json()

    yield from riders


def get_club_riders(club_id: int, use_json=False):
    if use_json:
        with open("data/raw/club_riders.json", "r") as f:
            riders = json.load(f)
    else:
        response = httpx.get(f"{BASE_URL}clubs/{club_id}", headers=HEADER)
        response.raise_for_status()
        riders = response.json().get("riders", [])

    yield from riders


if __name__ == "__main__":
    OFFLINE = True

    os.makedirs("data/raw", exist_ok=True)

    rider = [r for r in get_rider(4598636, use_json=OFFLINE)]
    with open("data/raw/rider.json", "w") as f:
        json.dump(rider, f)

    riders = [r for r in get_riders([4598636, 5574], use_json=OFFLINE)]
    with open("data/raw/riders.json", "w") as f:
        json.dump(riders, f)

    club_riders = [r for r in get_club_riders(20650, use_json=OFFLINE)]
    with open("data/raw/club_riders.json", "w") as f:
        json.dump(club_riders, f)
