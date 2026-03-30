"""Helper script: create a Daily.co room and print the URL."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def create_room() -> str:
    resp = requests.post(
        "https://api.daily.co/v1/rooms",
        headers={"Authorization": f"Bearer {os.environ['DAILY_API_KEY']}"},
        json={"properties": {"enable_prejoin_ui": False, "exp": 3600}},
    )
    resp.raise_for_status()
    url = resp.json()["url"]
    print(f"Room created: {url}")
    return url


if __name__ == "__main__":
    create_room()
