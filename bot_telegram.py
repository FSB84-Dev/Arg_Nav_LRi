import logging
import io
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from flujo_reuniones import procesar_audio_reunion, formatear_confirmacion

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
                    "Bot Automatizacion Comercial\n\n"
                    "Aragon - Navarra - La Rioja\n\n"
                    "Opciones disponibles:\n"
                    "/help - Ver ayuda\n"
                    "Envia un audio de reunion\n"
                    "Escribe una tarea rapida\n"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
                    "Ayuda\n\n"
                    "Audio de reunion: Graba y envia, se transcribe y guarda automaticamente\n"
                    "Tarea rapida: Escribe la tarea, aparece en Trello\n"
                    "Licitaciones: Recibes alertas automaticas cada manana\n"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        texto = update.message.text
        logger.info(f"Mensaje recibido: {texto}")
        await update.message.reply_text(
            "Mensaje recibido. Funcionalidad de tareas disponible pronto."
        )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Audio recibido - iniciando procesamiento")
        await update.message.reply_text("Audio recibido. Procesando...")

    try:
                if update.message.voice:
                                file_obj = await update.message.voice.get_file()
                                duracion = update.message.voice.duration
elif update.message.audio:
            file_obj = await update.message.audio.get_file()
            duracion = update.message.audio.duration or 0
else:
            await update.message.reply_text("Formato de audio no reconocido.")
                return

        audio_bytes = await file_obj.download_as_bytearray()
        resultado = await procesar_audio_reunion(bytes(audio_bytes), duracion=duracion)

        if resultado["ok"]:
                        confirmacion = formatear_confirmacion(resultado)
                        await update.message.reply_text(confirmacion)
else:
            await update.message.reply_text(
                                f"Error procesando audio: {resultado.get('error', 'desconocido')}\n"
                                "Por favor intenta de nuevo."
            )
except Exception as e:
        logger.error(f"Error en handle_audio: {e}")
        await update.message.reply_text("Error inesperado. Por favor intenta de nuevo.")

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
