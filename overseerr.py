import httpx
from config import OVERSEERR_URL, OVERSEERR_API_KEY

HEADERS = {
    "X-Api-Key": OVERSEERR_API_KEY,
    "Content-Type": "application/json",
}

STATUS_MAP = {
    1: "⏳ Pendiente",
    2: "✅ Aprobada",
    3: "❌ Rechazada",
    4: "🟢 Disponible",
    5: "🔄 Procesando",
}


async def search(query: str) -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{OVERSEERR_URL}/api/v1/search",
            params={"query": query, "language": "es"},
            headers=HEADERS,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        return [r for r in results if r.get("mediaType") in ("movie", "tv")][:8]


async def find_user_by_email(email: str) -> dict | None:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{OVERSEERR_URL}/api/v1/user",
            params={"take": 100},
            headers=HEADERS,
        )
        r.raise_for_status()
        users = r.json().get("results", [])
        email_lower = email.strip().lower()
        return next((u for u in users if u.get("email", "").lower() == email_lower), None)


async def request_media(media_type: str, media_id: int, overseerr_user_id: int | None = None) -> dict:
    payload = {"mediaType": media_type, "mediaId": media_id}
    if media_type == "tv":
        payload["seasons"] = "all"
    if overseerr_user_id:
        payload["userId"] = overseerr_user_id

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{OVERSEERR_URL}/api/v1/request",
            json=payload,
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


async def get_requests(take: int = 15, overseerr_user_id: int | None = None) -> list:
    params = {"take": take, "sort": "added"}
    if overseerr_user_id:
        params["requestedBy"] = overseerr_user_id

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{OVERSEERR_URL}/api/v1/request",
            params=params,
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json().get("results", [])
