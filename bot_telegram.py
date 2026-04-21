import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bot Automatización Comercial*\n\n"
        "Aragón · Navarra · La Rioja\n\n"
        "Opciones disponibles:\n"
        "/help - Ver ayuda\n"
        "🎙️ Envía un audio de reunión\n"
        "📝 Escribe una tarea rápida\n",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Ayuda*\n\n"
        "🎙️ *Audio de reunión:* Graba y envía, se transcribe y guarda automáticamente\n"
        "📝 *Tarea rápida:* Escribe la tarea, aparece en Trello\n"
        "📄 *Licitaciones:* Recibes alertas automáticas cada mañana\n",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    logger.info(f"Mensaje recibido: {texto}")
    await update.message.reply_text(
        f"✅ Mensaje recibido.\n"
        f"Funcionalidad completa disponible en próximas fases.",
    )

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Audio recibido")
    await update.message.reply_text(
        "🎙️ Audio recibido.\n"
        "Transcripción automática disponible en Fase 1."
    )

def main():
    logger.info("🚀 Bot iniciando...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
    logger.info("✅ Bot corriendo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
