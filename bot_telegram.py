import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from flujo_reuniones import procesar_audio_reunion, formatear_confirmacion

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                            "Bot Automatizacion Comercial\n\nAragon - Navarra - La Rioja\n\n"
                            "Opciones:\n/help - Ayuda\nEnvia audio de reunion\nEscribe una tarea"
            )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                            "Ayuda\n\nAudio: Graba y envia, se transcribe automaticamente\n"
                            "Tarea: Escribe, aparece en Trello\nLicitaciones: Alertas cada manana"
            )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.info(f"Mensaje: {update.message.text}")
            await update.message.reply_text("Mensaje recibido. Funcionalidad de tareas proximamente.")


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.info("Audio recibido")
            await update.message.reply_text("Audio recibido. Procesando...")
            try:
                            if update.message.voice:
                                                file_obj = await update.message.voice.get_file()
                                                duracion = update.message.voice.duration
elif update.message.audio:
            file_obj = await update.message.audio.get_file()
            duracion = update.message.audio.duration or 0
else:
            await update.message.reply_text("Formato no reconocido.")
                    return
        audio_bytes = await file_obj.download_as_bytearray()
        resultado = await procesar_audio_reunion(bytes(audio_bytes), duracion=duracion)
        if resultado["ok"]:
                            await update.message.reply_text(formatear_confirmacion(resultado))
else:
            await update.message.reply_text(f"Error: {resultado.get('error', 'desconocido')}")
except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Error inesperado. Intenta de nuevo.")


def main():
            logger.info("Bot iniciando...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    logger.info("Bot corriendo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
            main()
