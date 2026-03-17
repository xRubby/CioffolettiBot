from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler

from database.DAO.UtenteDAO import UtenteDAO
from database.Entity.Utente import Utente

PAGINA_SIZE = 5
ATTESA_RICERCA = 1  # stato conversazione


# ── Pannello admin ────────────────────────────────────────────────────────────

async def handler_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["pagina"] = 0
    await _mostra_lista(query, ctx)


# ── Lista utenti paginata ─────────────────────────────────────────────────────

async def _mostra_lista(query, ctx, utenti: list = None):
    pagina = ctx.user_data.get("pagina", 0)
    offset = pagina * PAGINA_SIZE

    if utenti is None:
        utenti = UtenteDAO.get_utenti_paginati(offset=offset, limit=PAGINA_SIZE)
        totale = UtenteDAO.conta_utenti()
    else:
        totale = len(utenti)

    righe = []
    for u in utenti:
        ruolo = "🛠" if u.is_admin else "👤"
        stato = "✅" if u.is_active else "🚫"
        label = f"{ruolo} {stato} @{u.telegram_username or u.telegram_user_id}"
        righe.append([InlineKeyboardButton(label, callback_data=f"impostazioni_admin_utente_{u.id}")])

    # Navigazione pagine
    nav = []
    if pagina > 0:
        nav.append(InlineKeyboardButton("◀️ Indietro", callback_data="impostazioni_admin_pagina_prec"))
    if offset + PAGINA_SIZE < totale:
        nav.append(InlineKeyboardButton("Avanti ▶️", callback_data="impostazioni_admin_pagina_succ"))
    if nav:
        righe.append(nav)

    righe.append([InlineKeyboardButton("🔍 Cerca utente", callback_data="cerca_utente")])
    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data="impostazioni")])

    await query.edit_message_text(
        f"👥 *Utenti registrati* — pagina {pagina + 1}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )


async def handler_pagina_prec(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["pagina"] = max(0, ctx.user_data.get("pagina", 1) - 1)
    await _mostra_lista(query, ctx)


async def handler_pagina_succ(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["pagina"] = ctx.user_data.get("pagina", 0) + 1
    await _mostra_lista(query, ctx)


# ── Scheda utente ─────────────────────────────────────────────────────────────

async def handler_utente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    utente_id = int(query.data.split("_")[-1])
    u = UtenteDAO.get_utente(utente_id)
    if not u:
        await query.answer("Utente non trovato.", show_alert=True)
        return

    ruolo_label = "Revoca admin 🛠" if u.is_admin else "Rendi admin 🛠"
    stato_label = "Disabilita 🚫" if u.is_active else "Abilita ✅"

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton(ruolo_label, callback_data=f"impostazioni_admin_toggle_admin_{u.id}")],
        [InlineKeyboardButton(stato_label, callback_data=f"impostazioni_admin_toggle_stato_{u.id}")],
        [InlineKeyboardButton("🔙 Lista utenti", callback_data="impostazioni_admin")],
    ])

    testo = (
        f"👤 <b>Utente:</b> <a href='tg://user?id={u.telegram_user_id}'>{u.telegram_username}</a>\n"
        f"🆔 <b>Telegram ID:</b> <code>{u.telegram_user_id}</code>\n"
        f"🛠 <b>Admin:</b> {'Sì' if u.is_admin else 'No'}\n"
        f"✅ <b>Attivo:</b> {'Sì' if u.is_active else 'No'}\n"
    )
    await query.edit_message_text(testo, parse_mode="HTML", reply_markup=tastiera)


# ── Toggle admin / stato ──────────────────────────────────────────────────────

async def handler_toggle_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    utente_id = int(query.data.split("_")[-1])
    u = UtenteDAO.get_utente(utente_id)
    if u.is_admin:
        UtenteDAO.disattiva_admin(utente_id)
    else:
        UtenteDAO.rendi_admin(utente_id)

    query.data = f"impostazioni_admin_utente_{utente_id}"
    await handler_utente(update, ctx)


async def handler_toggle_stato(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    utente_id = int(query.data.split("_")[-1])
    u = UtenteDAO.get_utente(utente_id)
    if u.is_active:
        UtenteDAO.rimuovi_utente(utente_id)
    else:
        UtenteDAO.riattiva_utente(utente_id)

    query.data = f"impostazioni_admin_utente_{utente_id}"
    await handler_utente(update, ctx)


# ── Ricerca utenti ────────────────────────────────────────────────────────────

async def handler_avvia_ricerca(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Lista utenti", callback_data="impostazioni_admin")]
    ])

    msg = await query.edit_message_text("🔍 Scrivi il nome utente da cercare:", reply_markup=tastiera)
    ctx.user_data["ricerca_message_id"] = msg.message_id
    return ATTESA_RICERCA


async def handler_esegui_ricerca(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    utenti = UtenteDAO.cerca_utenti(testo)

    await update.message.delete()

    message_id = ctx.user_data.pop("ricerca_message_id", None)

    if not utenti:
        tastiera = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Lista utenti", callback_data="impostazioni_admin")]
        ])
        await ctx.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text="Nessun utente trovato.",
            reply_markup=tastiera,
        )
        return ConversationHandler.END

    righe = []
    for u in utenti:
        ruolo = "🛠" if u.is_admin else "👤"
        stato = "✅" if u.is_active else "🚫"
        label = f"{ruolo} {stato} @{u.telegram_username or u.telegram_user_id}"
        righe.append([InlineKeyboardButton(label, callback_data=f"impostazioni_admin_utente_{u.id}")])

    righe.append([InlineKeyboardButton("🔙 Lista utenti", callback_data="impostazioni_admin")])
    await ctx.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=f"Risultati per *{testo}*:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )
    return ConversationHandler.END

async def _annulla_ricerca(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await handler_admin(update, ctx)
    return ConversationHandler.END


# ── ConversationHandler per la ricerca ───────────────────────────────────────

conv_ricerca = ConversationHandler(
    entry_points=[CallbackQueryHandler(handler_avvia_ricerca, pattern="^cerca_utente$")],
    states={ATTESA_RICERCA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_esegui_ricerca),
            CallbackQueryHandler(_annulla_ricerca, pattern="^impostazioni_admin$"),
        ]},
    fallbacks=[],
    per_message=False,
    per_chat=True,
)