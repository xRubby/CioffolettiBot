from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.DAO.UtenteDAO import UtenteDAO

async def handler_impostazioni(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    utente = UtenteDAO.get_utente_by_telegram_id(query.from_user.id)

    righe = [[InlineKeyboardButton("👤 Il mio profilo", callback_data="profilo")]]

    if utente and utente.is_admin:
        righe.append([InlineKeyboardButton("🛠️ Pannello Admin", callback_data="impostazioni_admin")])

    righe.append([InlineKeyboardButton("🔙 Menu principale", callback_data="menu_principale")])

    tastiera = InlineKeyboardMarkup(righe)
    await query.edit_message_text("⚙️ *Impostazioni*", parse_mode="Markdown", reply_markup=tastiera)

async def handler_profilo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    utente = update.effective_user

    u = UtenteDAO.get_utente_by_telegram_id(utente.id)
    if not u:
        await query.answer("Utente non trovato.", show_alert=True)
        return

    await query.answer()

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Indietro", callback_data="impostazioni")],
    ])

    testo = (
        f"👤 <b>Utente:</b> <a href='tg://user?id={u.telegram_user_id}'>{u.telegram_username}</a>\n"
        f"🆔 <b>Telegram ID:</b> `<a href='tg://user?id={u.telegram_user_id}'>{u.telegram_user_id}</a>`\n"
        f"🛠 <b>Admin:</b> {'Sì' if u.is_admin else 'No'}\n"
        f"✅ <b>Attivo:</b> {'Sì' if u.is_active else 'No'}\n"
    )
    await query.edit_message_text(testo, parse_mode="HTML", reply_markup=tastiera)