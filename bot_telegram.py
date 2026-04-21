import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from flujo_reuniones import procesar_audio_reunion, formatear_confirmacion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Comercial Aragon-Navarra-LaRioja\n/help para ayuda")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Envia audio de reunion o escribe una tarea")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Mensaje recibido.")


async def descargar_audio(update: Update):
    if update.message.voice:
        f = await update.message.voice.get_file()
        d = update.message.voice.duration
        b = await f.download_as_bytearray()
        return bytes(b), d
    elif update.message.audio:
        f = await update.message.audio.get_file()
        d = update.message.audio.duration or 0
        b = await f.download_as_bytearray()
        return bytes(b), d
    return None, 0


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Audio recibido. Procesando...")
    audio, dur = await descargar_audio(update)
    if audio is None:
        await update.message.reply_text("Formato no reconocido.")
        return
    resultado = await procesar_audio_reunion(audio, duracion=dur)
    if resultado["ok"]:
        await update.message.reply_text(formatear_confirmacion(resultado))
    else:
        await update.message.reply_text("Error procesando audio.")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    logger.info("Bot corriendo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
