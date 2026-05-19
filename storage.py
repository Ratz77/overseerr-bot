import json
import os

USERS_FILE = os.getenv("USERS_FILE", "users.json")


def _load() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_overseerr_id(telegram_id: int) -> int | None:
    data = _load()
    return data.get(str(telegram_id))


def link_user(telegram_id: int, overseerr_id: int):
    data = _load()
    data[str(telegram_id)] = overseerr_id
    _save(data)


def unlink_user(telegram_id: int):
    data = _load()
    data.pop(str(telegram_id), None)
    _save(data)
