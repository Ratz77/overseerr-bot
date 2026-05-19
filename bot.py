import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

import overseerr
import storage
from config import TELEGRAM_TOKEN, ALLOWED_USERS
from overseerr import STATUS_MAP

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return str(user_id) in ALLOWED_USERS


def get_title(item: dict) -> str:
    return item.get("title") or item.get("name") or "Sin título"


def get_year(item: dict) -> str:
    date = item.get("releaseDate") or item.get("firstAirDate") or ""
    return f" ({date[:4]})" if date else ""


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    overseerr_id = storage.get_overseerr_id(update.effective_user.id)
    vinculado = "✅ Vinculado a Overseerr" if overseerr_id else "⚠️ No vinculado — usa `/vincular tu@email.com`"

    await update.message.reply_text(
        "👋 *Bot de Overseerr*\n\n"
        f"Estado: {vinculado}\n\n"
        "Comandos disponibles:\n"
        "• `/vincular <email>` — Vincula tu cuenta de Overseerr\n"
        "• `/buscar <nombre>` — Busca película o serie y solicítala\n"
        "• `/peticiones` — Ver tus peticiones recientes\n"
        "• `/desvincular` — Desvincula tu cuenta de Overseerr\n",
        parse_mode="Markdown",
    )


async def cmd_vincular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    if not context.args:
        await update.message.reply_text(
            "Uso: `/vincular tu@email.com`\n\nIntroduce el email con el que estás registrado en Overseerr.",
            parse_mode="Markdown",
        )
        return

    email = context.args[0].strip()
    msg = await update.message.reply_text(f"🔍 Buscando cuenta con email *{email}*...", parse_mode="Markdown")

    try:
        user = await overseerr.find_user_by_email(email)

        if not user:
            await msg.edit_text(
                f"❌ No se encontró ningún usuario con el email *{email}* en Overseerr.\n\n"
                "Asegúrate de que el email es correcto y de que tienes cuenta en Overseerr.",
                parse_mode="Markdown",
            )
            return

        storage.link_user(update.effective_user.id, user["id"])
        display = user.get("displayName") or user.get("username") or email

        await msg.edit_text(
            f"✅ Cuenta vinculada correctamente.\n\n"
            f"👤 Usuario Overseerr: *{display}*\n"
            f"📧 Email: *{email}*\n\n"
            "A partir de ahora tus peticiones se harán en tu nombre.",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error vinculando usuario {email}: {e}")
        await msg.edit_text("❌ Error al conectar con Overseerr. Revisa la configuración.")


async def cmd_desvincular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    overseerr_id = storage.get_overseerr_id(update.effective_user.id)
    if not overseerr_id:
        await update.message.reply_text("No tienes ninguna cuenta vinculada.")
        return

    storage.unlink_user(update.effective_user.id)
    await update.message.reply_text("✅ Cuenta desvinculada correctamente.")


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
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
            label = f"{icon} {title}{year}"
            callback = f"req:{media_type}:{tmdb_id}:{title[:30]}"
            keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

        overseerr_id = storage.get_overseerr_id(update.effective_user.id)
        nota = "" if overseerr_id else "\n\n_⚠️ No vinculado: la petición se hará como invitado. Usa /vincular para asociar tu cuenta._"

        await msg.edit_text(
            f"Resultados para *{query}*:\n_Pulsa para solicitar:_{nota}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error buscando '{query}': {e}")
        await msg.edit_text("❌ Error al conectar con Overseerr. Revisa la configuración.")


async def callback_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_allowed(query.from_user.id):
        await query.edit_message_text("No tienes permiso.")
        return

    parts = query.data.split(":", 3)
    if len(parts) < 4:
        await query.edit_message_text("❌ Datos de solicitud inválidos.")
        return

    _, media_type, media_id_str, title = parts
    media_id = int(media_id_str)
    overseerr_user_id = storage.get_overseerr_id(query.from_user.id)

    await query.edit_message_text(f"⏳ Solicitando *{title}*...", parse_mode="Markdown")

    try:
        result = await overseerr.request_media(media_type, media_id, overseerr_user_id)
        status = STATUS_MAP.get(result.get("status", 1), "Desconocido")
        en_nombre = " (en tu nombre)" if overseerr_user_id else " (como invitado)"

        await query.edit_message_text(
            f"✅ *{title}* solicitada{en_nombre}.\nEstado: {status}",
            parse_mode="Markdown",
        )

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


async def cmd_peticiones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return

    overseerr_user_id = storage.get_overseerr_id(update.effective_user.id)
    msg = await update.message.reply_text("⏳ Cargando peticiones...")

    try:
        requests = await overseerr.get_requests(overseerr_user_id=overseerr_user_id)

        if not requests:
            await msg.edit_text("No tienes peticiones recientes.")
            return

        header = "📋 *Tus peticiones:*\n" if overseerr_user_id else "📋 *Peticiones recientes:*\n"
        lines = [header]
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


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN no está configurado en .env")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("vincular", cmd_vincular))
    app.add_handler(CommandHandler("desvincular", cmd_desvincular))
    app.add_handler(CommandHandler("buscar", cmd_buscar))
    app.add_handler(CommandHandler("peticiones", cmd_peticiones))
    app.add_handler(CallbackQueryHandler(callback_request, pattern=r"^req:"))

    logger.info("Bot arrancado. Escuchando...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
