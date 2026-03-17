from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.DAO.UtenteDAO import UtenteDAO

TESTO_HOME = (
    "⚫ *Bot Onoranze Funebri Cioffoletti*\n\n"
    "Benvenuto!\n"
    "Funzionalità in allestimento\n"
)

TASTIERA_HOME = InlineKeyboardMarkup([
    [InlineKeyboardButton("📋 Visualizza necrologi", callback_data="necrologi")],
    [InlineKeyboardButton("⚙️ Impostazioni", callback_data="impostazioni")],
])


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    utente = update.effective_user

    if not UtenteDAO.get_utente_by_telegram_id(utente.id):
        is_primo = UtenteDAO.conta_utenti() == 0
        UtenteDAO.aggiungi_utente(telegram_user_id=utente.id, username=utente.username or utente.first_name, is_admin=is_primo)
    else:
        UtenteDAO.aggiorna_nome(utente.id, utente.username or utente.first_name)

    await update.message.reply_text(TESTO_HOME, parse_mode="Markdown", reply_markup=TASTIERA_HOME)


async def handler_menu_principale(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(TESTO_HOME, parse_mode="Markdown", reply_markup=TASTIERA_HOME)