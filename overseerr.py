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


async def request_media(media_type: str, media_id: int) -> dict:
    payload = {"mediaType": media_type, "mediaId": media_id}
    if media_type == "tv":
        payload["seasons"] = "all"

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{OVERSEERR_URL}/api/v1/request",
            json=payload,
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json()


async def get_requests(take: int = 15) -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{OVERSEERR_URL}/api/v1/request",
            params={"take": take, "sort": "added"},
            headers=HEADERS,
        )
        r.raise_for_status()
        return r.json().get("results", [])
