import asyncio
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters,
)

import overseerr
import storage
import notifier
from config import TELEGRAM_TOKEN, ALLOWED_USERS, WARN_TURKISH, WARN_LATIN, WARN_TELENOVELA
from overseerr import STATUS_MAP

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WAITING_EMAIL = 1

NOT_AUTHORIZED_MSG = (
    "⛔ No estás autorizado para usar este bot.\n\n"
    "Vincula tu cuenta de Overseerr con:\n`/vincular`"
)

MEDIA_STATUS_LABEL = {
    2: "Ya está solicitada",
    3: "Procesando",
    4: "Parcialmente disponible",
    5: "Disponible en Plex",
}

SOAP_GENRE_ID = 10766

LATIN_COUNTRIES = {"MX", "AR", "CO", "VE", "PE", "CL", "EC", "BO", "PY", "UY", "CR", "PA", "HN", "GT", "SV", "DO", "CU", "PR"}

ORIGIN_WARNING = {
    "turca":      ("⚠️ Esta es una serie turca, es muy probable que la petición sea rechazada.",      lambda: WARN_TURKISH),
    "latina":     ("⚠️ Esta es una serie latina, es muy probable que la petición sea rechazada.",     lambda: WARN_LATIN),
    "telenovela": ("⚠️ Esta es una telenovela, es muy probable que la petición sea rechazada.",       lambda: WARN_TELENOVELA),
}


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return str(user_id) in ALLOWED_USERS


def is_linked(user_id: int) -> bool:
    return storage.get_overseerr_id(user_id) is not None


def get_title(item: dict) -> str:
    return item.get("title") or item.get("name") or "Sin título"


def get_year(item: dict) -> str:
    date = item.get("releaseDate") or item.get("firstAirDate") or ""
    return f" ({date[:4]})" if date else ""


def get_media_status_label(item: dict) -> str:
    status = (item.get("mediaInfo") or {}).get("status")
    return MEDIA_STATUS_LABEL.get(status, "")


def get_origin_key(item: dict) -> str:
    genre_ids = item.get("genreIds") or []
    countries = set(item.get("originCountry") or [])
    if SOAP_GENRE_ID in genre_ids:
        return "telenovela"
    if "TR" in countries:
        return "turca"
    if countries & LATIN_COUNTRIES:
        return "latina"
    return "0"


def get_origin_label(item: dict) -> str:
    key = get_origin_key(item)
    entry = ORIGIN_WARNING.get(key)
    if entry and entry[1]():
        return {"turca": "Serie turca", "latina": "Serie latina", "telenovela": "Telenovela"}.get(key, "")
    return ""


def user_display(user) -> str:
    return f"@{user.username}" if user.username else user.first_name


# ── /start ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    overseerr_id = storage.get_overseerr_id(update.effective_user.id)
    vinculado = "✅ Vinculado a Overseerr" if overseerr_id else "⚠️ No vinculado — usa `/vincular`"

    await update.message.reply_text(
        "👋 *Bot de Overseerr*\n\n"
        f"Estado: {vinculado}\n\n"
        "Comandos disponibles:\n"
        "• `/vincular` — Vincula tu cuenta de Overseerr\n"
        "• `/buscar <nombre>` — Busca película o serie y solicítala\n"
        "• `/peticiones` — Ver tus peticiones recientes\n"
        "• `/desvincular` — Desvincula tu cuenta de Overseerr\n",
        parse_mode="Markdown",
    )


async def cmd_start_vincular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point para el deep link /start vincular desde el grupo."""
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return ConversationHandler.END

    if is_linked(update.effective_user.id):
        await update.message.reply_text("Ya tienes una cuenta vinculada. Usa /desvincular primero si quieres cambiarla.")
        return ConversationHandler.END

    await update.message.reply_text("🔒 Introduce tu email de Overseerr para vincular tu cuenta:")
    return WAITING_EMAIL


# ── /vincular (ConversationHandler) ─────────────────────────────────────────

async def cmd_vincular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return ConversationHandler.END

    if is_linked(update.effective_user.id):
        await update.message.reply_text(
            "Ya tienes una cuenta vinculada. Usa /desvincular primero si quieres cambiarla."
        )
        return ConversationHandler.END

    in_group = update.effective_chat.type in ("group", "supergroup")

    if in_group:
        context.user_data["group_chat_id"] = update.effective_chat.id
        bot_username = (await context.bot.get_me()).username
        deep_link = f"https://t.me/{bot_username}?start=vincular"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔒 Vincular en privado", url=deep_link)
        ]])
        await update.message.reply_text(
            f"{user_display(update.effective_user)}, pulsa el botón para vincular tu cuenta de Overseerr en privado.",
            reply_markup=keyboard,
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "🔒 Introduce tu email de Overseerr para vincular tu cuenta:",
        )

    return WAITING_EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Solo atender en chat privado
    if update.effective_chat.type != "private":
        return WAITING_EMAIL

    email = update.message.text.strip()
    user = update.effective_user
    msg = await update.message.reply_text(f"🔍 Buscando cuenta con email *{email}*...", parse_mode="Markdown")

    try:
        overseerr_user = await overseerr.find_user_by_email(email)

        if not overseerr_user:
            await msg.edit_text(
                f"❌ No se encontró ningún usuario con el email *{email}* en Overseerr.\n\n"
                "Asegúrate de que el email es correcto y tienes cuenta en Overseerr.",
                parse_mode="Markdown",
            )
            return ConversationHandler.END

        storage.link_user(user.id, overseerr_user["id"])
        display = overseerr_user.get("displayName") or overseerr_user.get("username") or email

        await msg.edit_text(
            f"✅ Cuenta vinculada correctamente.\n\n"
            f"👤 Usuario Overseerr: *{display}*\n\n"
            "Ya puedes hacer peticiones desde el grupo o aquí en privado.",
            parse_mode="Markdown",
        )

        group_chat_id = context.user_data.pop("group_chat_id", None)
        if group_chat_id:
            await context.bot.send_message(
                chat_id=group_chat_id,
                text=f"✅ {user_display(user)} ya está vinculado y puede hacer peticiones.",
            )

    except Exception as e:
        logger.error(f"Error vinculando {email}: {e}")
        await msg.edit_text("❌ Error al conectar con Overseerr. Revisa la configuración.")

    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Vinculación cancelada.")
    return ConversationHandler.END


# ── /desvincular ─────────────────────────────────────────────────────────────

async def cmd_desvincular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    if not is_linked(update.effective_user.id):
        await update.message.reply_text("No tienes ninguna cuenta vinculada.")
        return

    storage.unlink_user(update.effective_user.id)
    await update.message.reply_text("✅ Cuenta desvinculada correctamente.")


# ── /buscar ──────────────────────────────────────────────────────────────────

async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    if not is_linked(update.effective_user.id):
        await update.message.reply_text(NOT_AUTHORIZED_MSG, parse_mode="Markdown")
        return

    if not context.args:
        await update.message.reply_text("Uso: `/buscar <nombre>`", parse_mode="Markdown")
        return

    query = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 Buscando *{query}*...", parse_mode="Markdown")

    try:
        results = await overseerr.search(query)

        if not results:
            await msg.edit_text(f"No se encontraron resultados para *{query}*.", parse_mode="Markdown")
            return

        keyboard = []
        for item in results:
            media_type = item.get("mediaType")
            title = get_title(item)
            year = get_year(item)
            icon = "🎬" if media_type == "movie" else "📺"
            tmdb_id = item.get("id")
            origin_label = get_origin_label(item)
            origin_key = get_origin_key(item)
            status_label = get_media_status_label(item)
            suffix = " · ".join(filter(None, [origin_label, status_label]))
            label = f"{icon} {title}{year}" + (f" · {suffix}" if suffix else "")
            callback = f"req:{media_type}:{tmdb_id}:{origin_key}:{title[:25]}"
            keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

        await msg.edit_text(
            f"Resultados para *{query}*:\n_Pulsa para solicitar:_",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error buscando '{query}': {e}")
        await msg.edit_text("❌ Error al conectar con Overseerr. Revisa la configuración.")


# ── callback petición ────────────────────────────────────────────────────────

async def callback_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_allowed(query.from_user.id):
        await query.edit_message_text("No tienes permiso.")
        return

    if not is_linked(query.from_user.id):
        await query.edit_message_text(NOT_AUTHORIZED_MSG, parse_mode="Markdown")
        return

    parts = query.data.split(":", 4)
    if len(parts) < 5:
        await query.edit_message_text("❌ Datos de solicitud inválidos.")
        return

    _, media_type, media_id_str, origin_key, title = parts
    media_id = int(media_id_str)
    overseerr_user_id = storage.get_overseerr_id(query.from_user.id)

    await query.edit_message_text(f"⏳ Solicitando *{title}*...", parse_mode="Markdown")

    try:
        result = await overseerr.request_media(media_type, media_id, overseerr_user_id)
        status = STATUS_MAP.get(result.get("status", 1), "Desconocido")
        warning_entry = ORIGIN_WARNING.get(origin_key)
        warning = warning_entry[0] if warning_entry and warning_entry[1]() else ""

        requester = user_display(query.from_user)
        text = f"✅ *{title}* solicitada por {requester}.\nEstado: {status}"
        if warning:
            text += f"\n\n{warning}"

        await query.edit_message_text(text, parse_mode="Markdown")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            await query.edit_message_text(
                f"ℹ️ *{title}* ya estaba solicitada o está disponible.",
                parse_mode="Markdown",
            )
        else:
            logger.error(f"HTTP {e.response.status_code} al solicitar '{title}': {e}")
            await query.edit_message_text("❌ Error al realizar la solicitud.")

    except Exception as e:
        logger.error(f"Error al solicitar '{title}': {e}")
        await query.edit_message_text("❌ Error al conectar con Overseerr.")


# ── /peticiones ──────────────────────────────────────────────────────────────

async def cmd_peticiones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    if not is_linked(update.effective_user.id):
        await update.message.reply_text(NOT_AUTHORIZED_MSG, parse_mode="Markdown")
        return

    overseerr_user_id = storage.get_overseerr_id(update.effective_user.id)
    msg = await update.message.reply_text("⏳ Cargando peticiones...")

    try:
        requests = await overseerr.get_requests(overseerr_user_id=overseerr_user_id)

        if not requests:
            await msg.edit_text("No tienes peticiones recientes.")
            return

        lines = ["📋 *Tus peticiones:*\n"]
        for req in requests:
            media = req.get("media", {})
            title = media.get("originalTitle") or media.get("originalName") or "Sin título"
            media_type = media.get("mediaType", "")
            icon = "🎬" if media_type == "movie" else "📺"
            status = STATUS_MAP.get(req.get("status", 1), "Desconocido")
            lines.append(f"{icon} *{title}* — {status}")

        await msg.edit_text("\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error obteniendo peticiones: {e}")
        await msg.edit_text("❌ Error al conectar con Overseerr.")


# ── arranque ─────────────────────────────────────────────────────────────────

async def post_init(app: Application):
    asyncio.create_task(notifier.run(app))
    logger.info("Notificador arrancado. Comprobará peticiones cada 12 horas.")


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN no está configurado en .env")

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("vincular", cmd_vincular),
            MessageHandler(
                filters.ChatType.PRIVATE & filters.Regex(r"^/start vincular"),
                cmd_start_vincular,
            ),
        ],
        states={
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive_email)],
        },
        fallbacks=[CommandHandler("cancelar", cmd_cancel)],
        per_chat=False,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("desvincular", cmd_desvincular))
    app.add_handler(CommandHandler("buscar", cmd_buscar))
    app.add_handler(CommandHandler("peticiones", cmd_peticiones))
    app.add_handler(CallbackQueryHandler(callback_request, pattern=r"^req:"))

    logger.info("Bot arrancado. Escuchando...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
