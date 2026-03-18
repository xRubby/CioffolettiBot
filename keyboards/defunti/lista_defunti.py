from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)

from database.DAO.DefuntoDAO import DefuntoDAO
from database.DAO.UtenteDAO import UtenteDAO
from config import Stato

PAGINA_SIZE = 5
ATTESA_RICERCA_DEFUNTO = 1


# ── Lista defunti paginata ────────────────────────────────────────────────────

async def handler_lista_defunti(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("necrologi_lista_p_"):
        pagina = int(data.split("_")[-1])
    else:
        pagina = 0

    ctx.user_data["lista_defunti_pagina"] = pagina

    dao = DefuntoDAO()
    offset = pagina * PAGINA_SIZE
    totale = dao.conta_defunti()
    defunti_pagina = dao.get_defunti_paginati(offset=offset, limit=PAGINA_SIZE)

    if not defunti_pagina and pagina == 0:
        tastiera = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Aggiungi defunto", callback_data="necrologi_aggiungi")],
            [InlineKeyboardButton("🔙 Indietro", callback_data="necrologi")],
        ])
        await query.edit_message_text(
            "📋 *Lista defunti*\n\nNessun defunto presente.",
            parse_mode="Markdown",
            reply_markup=tastiera,
        )
        return

    righe = []
    righe.append([InlineKeyboardButton("🔍 Cerca defunto", callback_data="necrologi_cerca_defunto")])
    for d in defunti_pagina:
        label = f"🪦 {d.cognome} {d.nome} — {d.data_decesso.strftime('%d/%m/%Y')}"
        righe.append([InlineKeyboardButton(label, callback_data=f"necrologi_scheda_{d.id}")])

    n_pagine = -(-totale // PAGINA_SIZE)

    nav = []
    if pagina > 0:
        if n_pagine >= 3:
            nav.append(InlineKeyboardButton("⏮️", callback_data="necrologi_lista_p_0"))
        nav.append(InlineKeyboardButton("◀️ Prec", callback_data=f"necrologi_lista_p_{pagina - 1}"))
    if offset + PAGINA_SIZE < totale:
        nav.append(InlineKeyboardButton("Succ ▶️", callback_data=f"necrologi_lista_p_{pagina + 1}"))
        if n_pagine >= 3:
            nav.append(InlineKeyboardButton("⏭️", callback_data=f"necrologi_lista_p_{n_pagine - 1}"))
    if nav:
        righe.append(nav)

    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data="necrologi")])

    await query.edit_message_text(
        f"📋 *Lista defunti* — pagina {pagina + 1} ({totale} totali)",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )


# ── Ricerca defunti ───────────────────────────────────────────────────────────

async def handler_avvia_ricerca_defunto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Lista defunti", callback_data="necrologi_lista")]
    ])
    msg = await query.edit_message_text(
        "🔍 Scrivi il nome, cognome o entrambi da cercare:",
        reply_markup=tastiera,
    )
    ctx.user_data["ricerca_defunto_msg_id"] = msg.message_id
    return ATTESA_RICERCA_DEFUNTO


async def handler_esegui_ricerca_defunto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()

    message_id = ctx.user_data.pop("ricerca_defunto_msg_id", None)
    defunti = DefuntoDAO().cerca_defunti(testo)

    tastiera_back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Lista defunti", callback_data="necrologi_lista")]
    ])

    if not defunti:
        await ctx.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            text=f"Nessun defunto trovato per *{testo}*.",
            parse_mode="Markdown",
            reply_markup=tastiera_back,
        )
        return ConversationHandler.END

    righe = []
    for d in defunti:
        label = f"🪦 {d.cognome} {d.nome} — {d.data_decesso.strftime('%d/%m/%Y')}"
        righe.append([InlineKeyboardButton(label, callback_data=f"necrologi_scheda_{d.id}")])
    righe.append([InlineKeyboardButton("🔙 Lista defunti", callback_data="necrologi_lista")])

    await ctx.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=f"🔍 Risultati per *{testo}* ({len(defunti)} trovati):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )
    return ConversationHandler.END


async def _annulla_ricerca_defunto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("ricerca_defunto_msg_id", None)
    await handler_lista_defunti(update, ctx)
    return ConversationHandler.END


conv_ricerca_defunto = ConversationHandler(
    entry_points=[CallbackQueryHandler(handler_avvia_ricerca_defunto, pattern="^necrologi_cerca_defunto$")],
    states={
        ATTESA_RICERCA_DEFUNTO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_esegui_ricerca_defunto),
            CallbackQueryHandler(_annulla_ricerca_defunto, pattern=r"^necrologi_lista(_p_\d+)?$"),
        ]
    },
    fallbacks=[],
    per_message=False,
    per_chat=True,
)


# ── Scheda singolo defunto ────────────────────────────────────────────────────

async def handler_scheda_defunto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    defunto_id = int(query.data.split("_")[-1])
    d = DefuntoDAO().get_defunto(defunto_id)

    if not d:
        await query.answer("Defunto non trovato.", show_alert=True)
        return

    aggiunto_da_utente = UtenteDAO.get_utente(d.aggiunto_da)
    if aggiunto_da_utente:
        aggiunto_da_str = (
            f"<a href='tg://user?id={aggiunto_da_utente.telegram_user_id}'>"
            f"@{aggiunto_da_utente.telegram_username or aggiunto_da_utente.telegram_user_id}</a>"
            f" (ID: <code>{aggiunto_da_utente.telegram_user_id}</code>)"
        )
    else:
        aggiunto_da_str = f"<code>{d.aggiunto_da}</code>"

    telefono_str = d.telefono_delegante if d.telefono_delegante else "—"

    nome_del_str = d.nome_delegante if d.nome_delegante else "—"
    note_str     = d.note if d.note else "—"

    testo = (
        f"🪦 <b>{d.cognome} {d.nome}</b>\n\n"
        f"📅 <b>Data decesso:</b> {d.data_decesso.strftime('%d/%m/%Y')}\n"
        f"📞 <b>Telefono delegante:</b> {telefono_str}\n"
        f"👤 <b>Nome delegante:</b> {nome_del_str}\n"
        f"🗓 <b>Inserito il:</b> {d.creato_il.strftime('%d/%m/%Y')}\n"
        f"👤 <b>Aggiunto da:</b> {aggiunto_da_str}\n\n"
        f"📬 <b>Ringraziamento:</b> {Stato.EMOJI[d.stato_ringraziamento]}\n"
        f"🙏 <b>Preci:</b> {Stato.EMOJI[d.stato_preci]}\n"
        f"📿 <b>Trigesimo:</b> {Stato.EMOJI[d.stato_trigesimo]}\n\n"
        f"📝 <b>Note:</b> {note_str}\n"
    )

    pagina = ctx.user_data.get("lista_defunti_pagina", 0)

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Anniversari", callback_data=f"anniv_lista_{defunto_id}")],
        [InlineKeyboardButton("✏️ Modifica informazioni", callback_data=f"necrologi_modifica_{defunto_id}")],
        [InlineKeyboardButton("🔙 Lista defunti", callback_data=f"necrologi_lista_p_{pagina}")],
    ])

    await query.edit_message_text(testo, parse_mode="HTML", reply_markup=tastiera)