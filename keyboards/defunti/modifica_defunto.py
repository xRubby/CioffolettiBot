from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from datetime import date

from database.DAO.DefuntoDAO import DefuntoDAO
from config import Stato

# ── Stati conversazione ───────────────────────────────────────────────────────
MENU, ATTESA_VALORE = range(2)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _edit(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, testo: str,
                tastiera=None, parse_mode="Markdown"):
    await ctx.bot.edit_message_text(
        chat_id=chat_id,
        message_id=ctx.user_data["modifica_msg_id"],
        text=testo,
        parse_mode=parse_mode,
        reply_markup=tastiera,
    )


def _tastiera_menu_modifica(defunto_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Nome",             callback_data=f"necrologi_mod_nome_{defunto_id}"),
         InlineKeyboardButton("✏️ Cognome",          callback_data=f"necrologi_mod_cognome_{defunto_id}"),
        InlineKeyboardButton("📅 Data decesso",     callback_data=f"necrologi_mod_data_{defunto_id}")],
        [InlineKeyboardButton("📞 Telefono",         callback_data=f"necrologi_mod_telefono_{defunto_id}"),
        InlineKeyboardButton("👤 Delegante",        callback_data=f"necrologi_mod_delegante_{defunto_id}"),
         InlineKeyboardButton("📝 Note",             callback_data=f"necrologi_mod_note_{defunto_id}")],
        [InlineKeyboardButton("📬 Ringraziamento",   callback_data=f"necrologi_mod_ringraziamento_{defunto_id}"),
         InlineKeyboardButton("🙏 Preci",            callback_data=f"necrologi_mod_preci_{defunto_id}"),
         InlineKeyboardButton("📿 Trigesimo",        callback_data=f"necrologi_mod_trigesimo_{defunto_id}")],
        [InlineKeyboardButton("🗑️ Elimina defunto",  callback_data=f"necrologi_elimina_chiedi_{defunto_id}")],
        [InlineKeyboardButton("🔙 Scheda defunto",   callback_data=f"necrologi_scheda_{defunto_id}")],
    ])


def _tastiera_annulla(defunto_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Indietro", callback_data=f"necrologi_modifica_{defunto_id}")]
    ])


def _tastiera_stato(defunto_id: int, campo: str) -> InlineKeyboardMarkup:
    righe = [
        [InlineKeyboardButton(label, callback_data=f"necrologi_mod_stato_{campo}_{stato}_{defunto_id}")]
        for stato, label in Stato.EMOJI.items()
    ]
    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data=f"necrologi_modifica_{defunto_id}")])
    return InlineKeyboardMarkup(righe)


async def _mostra_menu(ctx, chat_id: int, defunto_id: int, prefisso: str = ""):
    d = DefuntoDAO().get_defunto(defunto_id)
    testo = (
        f"{prefisso}"
        f"✏️ *Modifica — {d.cognome} {d.nome}*\n\n"
        "Scegli il campo da modificare:"
    )
    await ctx.bot.edit_message_text(
        chat_id=chat_id,
        message_id=ctx.user_data["modifica_msg_id"],
        text=testo,
        parse_mode="Markdown",
        reply_markup=_tastiera_menu_modifica(defunto_id),
    )


# ── Entry point: apre il menu modifica ───────────────────────────────────────

async def handler_menu_modifica(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_msg_id"] = query.message.message_id

    await _mostra_menu(ctx, update.effective_chat.id, defunto_id)
    return MENU


# ── Stato MENU: scelta campo ──────────────────────────────────────────────────

async def handler_mod_nome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_campo"] = "nome"
    await _edit(ctx, update.effective_chat.id,
                "✏️ *Modifica Nome*\n\nInvia il nuovo nome:",
                tastiera=_tastiera_annulla(defunto_id))
    return ATTESA_VALORE


async def handler_mod_cognome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_campo"] = "cognome"
    await _edit(ctx, update.effective_chat.id,
                "✏️ *Modifica Cognome*\n\nInvia il nuovo cognome:",
                tastiera=_tastiera_annulla(defunto_id))
    return ATTESA_VALORE


async def handler_mod_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_campo"] = "data_decesso"
    await _edit(ctx, update.effective_chat.id,
                "✏️ *Modifica Data decesso*\n\nFormato: *GG/MM/AAAA*\nInvia la nuova data:",
                tastiera=_tastiera_annulla(defunto_id))
    return ATTESA_VALORE


async def handler_mod_telefono(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_campo"] = "telefono_delegante"
    await _edit(ctx, update.effective_chat.id,
                "✏️ *Modifica Telefono delegante*\n\nSolo cifre, es. `3331234567`.\nInvia `nessuno` per rimuoverlo:",
                tastiera=_tastiera_annulla(defunto_id))
    return ATTESA_VALORE


async def handler_mod_ringraziamento(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    await query.edit_message_text(
        "📬 *Ringraziamento* — scegli il nuovo stato:",
        parse_mode="Markdown",
        reply_markup=_tastiera_stato(defunto_id, "ringraziamento"),
    )
    return MENU


async def handler_mod_preci(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    await query.edit_message_text(
        "🙏 *Preci* — scegli il nuovo stato:",
        parse_mode="Markdown",
        reply_markup=_tastiera_stato(defunto_id, "preci"),
    )
    return MENU


async def handler_mod_trigesimo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    await query.edit_message_text(
        "📿 *Trigesimo* — scegli il nuovo stato:",
        parse_mode="Markdown",
        reply_markup=_tastiera_stato(defunto_id, "trigesimo"),
    )
    return MENU

async def handler_mod_delegante(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_campo"] = "nome_delegante"
    await _edit(ctx, update.effective_chat.id,
                "✏️ *Modifica Nome delegante*\n\nInvia il nuovo nome, o `nessuno` per rimuoverlo:",
                tastiera=_tastiera_annulla(defunto_id))
    return ATTESA_VALORE


async def handler_mod_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_campo"] = "note"
    await _edit(ctx, update.effective_chat.id,
                "✏️ *Modifica Note*\n\nInvia le nuove note, o `nessuno` per rimuoverle:",
                tastiera=_tastiera_annulla(defunto_id))
    return ATTESA_VALORE


async def handler_salva_stato(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: necrologi_mod_stato_{campo}_{stato}_{defunto_id}"""
    query = update.callback_query
    await query.answer()

    parti = query.data.split("_")
    defunto_id = int(parti[-1])
    campo = parti[3]
    stato = "_".join(parti[4:-1])

    DefuntoDAO().aggiorna_stato(defunto_id, f"stato_{campo}", stato)

    ctx.user_data["modifica_defunto_id"] = defunto_id
    ctx.user_data["modifica_msg_id"] = query.message.message_id
    await _mostra_menu(ctx, update.effective_chat.id, defunto_id, prefisso="✅ *Salvato!*\n\n")
    return MENU


# ── Elimina defunto ───────────────────────────────────────────────────────────

async def handler_elimina_chiedi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Mostra la schermata di conferma eliminazione."""
    query = update.callback_query
    await query.answer()

    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["modifica_msg_id"] = query.message.message_id
    d = DefuntoDAO().get_defunto(defunto_id)

    tastiera = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sì, elimina",  callback_data=f"necrologi_elimina_conferma_{defunto_id}"),
            InlineKeyboardButton("❌ No, annulla",  callback_data=f"necrologi_modifica_{defunto_id}"),
        ]
    ])

    await query.edit_message_text(
        f"🗑️ *Eliminare il defunto?*\n\n"
        f"Stai per eliminare *{d.cognome} {d.nome}* "
        f"(deceduto il {d.data_decesso.strftime('%d/%m/%Y')}).\n\n"
        f"⚠️ L'operazione è *irreversibile*.",
        parse_mode="Markdown",
        reply_markup=tastiera,
    )
    return MENU


async def handler_elimina_conferma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Esegue l'eliminazione e riporta alla lista defunti."""
    query = update.callback_query
    await query.answer()

    defunto_id = int(query.data.split("_")[-1])
    DefuntoDAO().elimina_defunto(defunto_id)

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Lista defunti", callback_data="necrologi_lista")]
    ])
    await query.edit_message_text(
        "✅ *Defunto eliminato con successo.*",
        parse_mode="Markdown",
        reply_markup=tastiera,
    )
    return ConversationHandler.END


# ── Stato ATTESA_VALORE: ricezione testo ──────────────────────────────────────

async def handler_ricevi_valore(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()

    defunto_id = ctx.user_data["modifica_defunto_id"]
    campo      = ctx.user_data["modifica_campo"]
    chat_id    = update.effective_chat.id
    dao        = DefuntoDAO()

    if campo == "nome":
        if not testo:
            await _edit(ctx, chat_id, "⚠️ Il nome non può essere vuoto. Riprova:",
                        tastiera=_tastiera_annulla(defunto_id))
            return ATTESA_VALORE
        dao.aggiorna_campo(defunto_id, "nome", testo.title())

    elif campo == "cognome":
        if not testo:
            await _edit(ctx, chat_id, "⚠️ Il cognome non può essere vuoto. Riprova:",
                        tastiera=_tastiera_annulla(defunto_id))
            return ATTESA_VALORE
        dao.aggiorna_campo(defunto_id, "cognome", testo.title())

    elif campo == "data_decesso":
        try:
            g, m, a = testo.split("/")
            data = date(int(a), int(m), int(g))
            if data > date.today():
                raise ValueError
        except (ValueError, TypeError):
            await _edit(ctx, chat_id,
                        "⚠️ Data non valida o futura. Usa il formato *GG/MM/AAAA*:",
                        tastiera=_tastiera_annulla(defunto_id))
            return ATTESA_VALORE
        dao.aggiorna_campo(defunto_id, "data_decesso", data.isoformat())

    elif campo == "telefono_delegante":
        if testo.lower() == "nessuno":
            dao.aggiorna_campo(defunto_id, "telefono_delegante", None)
        elif not testo.lstrip("+").isdigit() or len(testo) < 6:
            await _edit(ctx, chat_id,
                        "⚠️ Numero non valido. Solo cifre (es. `3331234567`) o `nessuno`:",
                        tastiera=_tastiera_annulla(defunto_id))
            return ATTESA_VALORE
        else:
            dao.aggiorna_campo(defunto_id, "telefono_delegante", testo)

    elif campo == "nome_delegante":
        dao.aggiorna_campo(defunto_id, "nome_delegante",
                        None if testo.lower() == "nessuno" else testo.title())

    elif campo == "note":
        dao.aggiorna_campo(defunto_id, "note",
                        None if testo.lower() == "nessuno" else testo)

    await _mostra_menu(ctx, chat_id, defunto_id, prefisso="✅ *Salvato!*\n\n")
    return MENU


# ── ConversationHandler ───────────────────────────────────────────────────────

conv_modifica_defunto = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handler_menu_modifica, pattern=r"^necrologi_modifica_\d+$"),
    ],
    states={
        MENU: [
            CallbackQueryHandler(handler_mod_nome,           pattern=r"^necrologi_mod_nome_\d+$"),
            CallbackQueryHandler(handler_mod_cognome,        pattern=r"^necrologi_mod_cognome_\d+$"),
            CallbackQueryHandler(handler_mod_data,           pattern=r"^necrologi_mod_data_\d+$"),
            CallbackQueryHandler(handler_mod_telefono,       pattern=r"^necrologi_mod_telefono_\d+$"),
            CallbackQueryHandler(handler_mod_ringraziamento, pattern=r"^necrologi_mod_ringraziamento_\d+$"),
            CallbackQueryHandler(handler_mod_preci,          pattern=r"^necrologi_mod_preci_\d+$"),
            CallbackQueryHandler(handler_mod_trigesimo,      pattern=r"^necrologi_mod_trigesimo_\d+$"),
            CallbackQueryHandler(handler_salva_stato,        pattern=r"^necrologi_mod_stato_.+_\d+$"),
            CallbackQueryHandler(handler_elimina_chiedi,     pattern=r"^necrologi_elimina_chiedi_\d+$"),
            CallbackQueryHandler(handler_elimina_conferma,   pattern=r"^necrologi_elimina_conferma_\d+$"),
            CallbackQueryHandler(handler_menu_modifica,      pattern=r"^necrologi_modifica_\d+$"),
            CallbackQueryHandler(handler_mod_delegante,      pattern=r"^necrologi_mod_delegante_\d+$"),
            CallbackQueryHandler(handler_mod_note,           pattern=r"^necrologi_mod_note_\d+$"),
        ],
        ATTESA_VALORE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_ricevi_valore),
            CallbackQueryHandler(handler_menu_modifica,    pattern=r"^necrologi_modifica_\d+$"),
            CallbackQueryHandler(handler_elimina_chiedi,   pattern=r"^necrologi_elimina_chiedi_\d+$"),
            CallbackQueryHandler(handler_elimina_conferma, pattern=r"^necrologi_elimina_conferma_\d+$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handler_menu_modifica, pattern=r"^necrologi_modifica_\d+$"),
    ],
    per_message=False,
    per_chat=True,
)