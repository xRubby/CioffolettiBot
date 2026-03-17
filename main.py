from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
from config import TELEGRAM_TOKEN
from database.Connessione import db_connection

from keyboards.main_menu import cmd_start

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Imposta la variabile d'ambiente TELEGRAM_TOKEN")
    
    db_connection.init_schema()
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))

    logger.info("Bot Cioffoletti avviato.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
 
 
if __name__ == "__main__":
    main()