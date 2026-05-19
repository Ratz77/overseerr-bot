import json
import os

USERS_FILE = os.getenv("USERS_FILE", "users.json")
STATES_FILE = os.getenv("STATES_FILE", "states.json")


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_overseerr_id(telegram_id: int) -> int | None:
    data = _load(USERS_FILE)
    return data.get(str(telegram_id))


def get_all_users() -> dict:
    """Returns {str(telegram_id): overseerr_user_id}"""
    return _load(USERS_FILE)


def link_user(telegram_id: int, overseerr_id: int):
    data = _load(USERS_FILE)
    data[str(telegram_id)] = overseerr_id
    _save(USERS_FILE, data)


def unlink_user(telegram_id: int):
    data = _load(USERS_FILE)
    data.pop(str(telegram_id), None)
    _save(USERS_FILE, data)


def get_states(overseerr_user_id: int) -> dict:
    """Returns {request_id: {status, title}} for a given Overseerr user."""
    data = _load(STATES_FILE)
    return data.get(str(overseerr_user_id), {})


def save_states(overseerr_user_id: int, states: dict):
    data = _load(STATES_FILE)
    data[str(overseerr_user_id)] = states
    _save(STATES_FILE, data)
