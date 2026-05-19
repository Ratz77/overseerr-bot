import asyncio
import logging

import overseerr
import storage
from overseerr import STATUS_MAP

logger = logging.getLogger(__name__)

POLL_INTERVAL = 12 * 3600  # 12 horas en segundos

NOTIFY_STATUSES = {2, 3, 4, 5}  # estados que generan notificación

NOTIFY_MESSAGES = {
    2: "✅ Tu petición de *{title}* ha sido aprobada.",
    3: "❌ Tu petición de *{title}* ha sido rechazada.",
    4: "🟢 *{title}* ya está disponible.",
    5: "🔄 *{title}* está siendo procesada.",
}


def _extract(req: dict) -> tuple[str, str]:
    media = req.get("media", {})
    title = media.get("originalTitle") or media.get("originalName") or "Sin título"
    media_type = media.get("mediaType", "")
    icon = "🎬" if media_type == "movie" else "📺"
    return f"{icon} {title}", str(req["id"])


async def _check_user(app, telegram_id: int, overseerr_user_id: int):
    requests = await overseerr.get_requests(overseerr_user_id=overseerr_user_id)

    current_states = {
        req_id: {"status": req["status"], "title": title}
        for req in requests
        for title, req_id in [_extract(req)]
    }

    saved_states = storage.get_states(overseerr_user_id)

    if not saved_states:
        storage.save_states(overseerr_user_id, current_states)
        logger.info(f"Estado inicial guardado para usuario Overseerr {overseerr_user_id}.")
        return

    for req_id, current in current_states.items():
        saved = saved_states.get(req_id)
        if saved and saved["status"] != current["status"] and current["status"] in NOTIFY_STATUSES:
            template = NOTIFY_MESSAGES.get(current["status"])
            if template:
                text = template.format(title=current["title"])
                await app.bot.send_message(chat_id=telegram_id, text=text, parse_mode="Markdown")
                logger.info(f"Notificado a {telegram_id}: {current['title']} → estado {current['status']}")

    storage.save_states(overseerr_user_id, current_states)


async def check_all(app):
    users = storage.get_all_users()
    if not users:
        return

    logger.info(f"Comprobando peticiones de {len(users)} usuario(s)...")
    for telegram_id_str, overseerr_user_id in users.items():
        try:
            await _check_user(app, int(telegram_id_str), overseerr_user_id)
        except Exception as e:
            logger.error(f"Error comprobando usuario {telegram_id_str}: {e}")


async def run(app):
    while True:
        await check_all(app)
        await asyncio.sleep(POLL_INTERVAL)
