from telegram import Update
from telegram.ext import ContextTypes


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = (
        "⚫ *Bot Onoranze Funebri Cioffoletti*\n\n"
        "Benvenuto!\n"
        "Funzionalità in allestimento\n"
    )
    await update.message.reply_text(testo, parse_mode="Markdown")
    