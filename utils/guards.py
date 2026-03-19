import re
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ApplicationHandlerStop
from database.DAO.UtenteDAO import UtenteDAO

_CACHE_KEY = "_utente_attivo"
_CACHE_TTL = 300  # secondi

_PATTERN_NECROLOGI = re.compile(r"^(necrologi|anniv)")


async def utente_attivo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    now = time.monotonic()
    cached = ctx.user_data.get(_CACHE_KEY)

    if cached and now - cached["ts"] < _CACHE_TTL:
        attivo = cached["attivo"]
    else:
        utente = UtenteDAO.get_utente_by_telegram_id(update.effective_user.id)
        attivo = bool(utente and utente.is_active)
        ctx.user_data[_CACHE_KEY] = {"attivo": attivo, "ts": now}

    if not attivo:
        tastiera = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Menu principale", callback_data="menu_principale")]
        ])
        if update.callback_query:
            await update.callback_query.answer("🚫 Account non attivo.", show_alert=True)
        elif update.message:
            await update.message.reply_text(
                "🚫 *Accesso negato*\n\nContatta un amministratore.",
                parse_mode="Markdown",
                reply_markup=tastiera,
            )
    return attivo


async def _check_necrologi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await utente_attivo(update, ctx):
        raise ApplicationHandlerStop
    


_PATTERN_ADMIN = re.compile(r"^(impostazioni_admin|cerca_utente)")

async def utente_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    utente = UtenteDAO.get_utente_by_telegram_id(update.effective_user.id)
    admin = bool(utente and utente.is_admin)

    if not admin and update.callback_query:
        await update.callback_query.answer("🚫 Accesso riservato agli amministratori.", show_alert=True)

    return admin


async def _check_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await utente_admin(update, ctx):
        raise ApplicationHandlerStop


gate_admin = CallbackQueryHandler(_check_admin, pattern=_PATTERN_ADMIN)


gate_necrologi = CallbackQueryHandler(_check_necrologi, pattern=_PATTERN_NECROLOGI)




