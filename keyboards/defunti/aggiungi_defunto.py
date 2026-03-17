from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from datetime import date
from database.DAO.DefuntoDAO import DefuntoDAO
from database.DAO.UtenteDAO import UtenteDAO

from keyboards.defunti.handle_defunti import handler_defunti

# Stati della conversazione
NOME, COGNOME, DATA_DECESSO, TELEFONO, NOME_DELEGANTE, NOTE, CONFERMA = range(7)

TASTO_ANNULLA = InlineKeyboardMarkup([
    [InlineKeyboardButton("❌ Annulla", callback_data="necrologi_aggiungi_annulla")]
])

TASTO_DATA = InlineKeyboardMarkup([
    [InlineKeyboardButton("📅 Oggi", callback_data="necrologi_aggiungi_oggi")],
    [InlineKeyboardButton("❌ Annulla", callback_data="necrologi_aggiungi_annulla")],
])

TASTO_TELEFONO = InlineKeyboardMarkup([
    [InlineKeyboardButton("🚫 Nessuno", callback_data="necrologi_aggiungi_tel_nessuno")],
    [InlineKeyboardButton("❌ Annulla", callback_data="necrologi_aggiungi_annulla")],
])

TASTO_SKIP_ANNULLA = InlineKeyboardMarkup([
    [InlineKeyboardButton("⏭ Salta", callback_data="necrologi_aggiungi_salta")],
    [InlineKeyboardButton("❌ Annulla", callback_data="necrologi_aggiungi_annulla")],
])


async def _edit(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, testo: str,
                tastiera=TASTO_ANNULLA, parse_mode="Markdown"):
    """Modifica il messaggio bot salvato in user_data."""
    await ctx.bot.edit_message_text(
        chat_id=chat_id,
        message_id=ctx.user_data["msg_id"],
        text=testo,
        parse_mode=parse_mode,
        reply_markup=tastiera,
    )


# ── Step 1: avvio ─────────────────────────────────────────────────────────────

async def handler_avvia_aggiungi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data.clear()

    msg = await query.edit_message_text(
        "➕ *Aggiungi defunto*\n\n"
        "Passo 1/6 — Inserisci il *nome*:",
        parse_mode="Markdown",
        reply_markup=TASTO_ANNULLA,
    )
    ctx.user_data["msg_id"] = msg.message_id
    return NOME


# ── Step 2: cognome ───────────────────────────────────────────────────────────

async def handler_nome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text.strip()
    await update.message.delete()

    if not nome:
        await _edit(ctx, update.effective_chat.id,
                    "⚠️ Il nome non può essere vuoto. Riprova:\n\nPasso 1/6 — Inserisci il *nome*:")
        return NOME

    ctx.user_data["nome"] = nome.title()
    await _edit(ctx, update.effective_chat.id,
                "Passo 2/6 — Inserisci il *cognome*:")
    return COGNOME


# ── Step 3: data decesso ──────────────────────────────────────────────────────

async def handler_cognome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cognome = update.message.text.strip()
    await update.message.delete()

    if not cognome:
        await _edit(ctx, update.effective_chat.id,
                    "⚠️ Il cognome non può essere vuoto. Riprova:\n\nPasso 2/6 — Inserisci il *cognome*:")
        return COGNOME

    ctx.user_data["cognome"] = cognome.title()
    await _edit(ctx, update.effective_chat.id,
                "Passo 3/6 — Inserisci la *data di decesso* (GG/MM/AAAA):",
                tastiera=TASTO_DATA)
    return DATA_DECESSO


# ── Step 4: telefono ──────────────────────────────────────────────────────────

async def handler_data_decesso(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()

    try:
        giorno, mese, anno = testo.split("/")
        data = date(int(anno), int(mese), int(giorno))
    except (ValueError, TypeError):
        await _edit(ctx, update.effective_chat.id,
                    "⚠️ Formato non valido. Inserisci la data come *GG/MM/AAAA* (es. 15/03/2025):\n\n"
                    "Passo 3/6 — Inserisci la *data di decesso*:",
                    tastiera=TASTO_DATA)
        return DATA_DECESSO

    if data > date.today():
        await _edit(ctx, update.effective_chat.id,
                    "⚠️ La data non può essere nel futuro. Riprova:\n\n"
                    "Passo 3/6 — Inserisci la *data di decesso* (GG/MM/AAAA):",
                    tastiera=TASTO_DATA)
        return DATA_DECESSO

    ctx.user_data["data_decesso"] = data
    await _edit(ctx, update.effective_chat.id,
                "Passo 4/4 — Inserisci il *telefono del delegante*:",
                tastiera=TASTO_TELEFONO)
    return TELEFONO


async def handler_data_oggi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["data_decesso"] = date.today()
    await _edit(ctx, update.effective_chat.id,
                "Passo 4/6 — Inserisci il *telefono del delegante*:",
                tastiera=TASTO_TELEFONO)
    return TELEFONO


# ── Step 5: riepilogo e conferma ──────────────────────────────────────────────

async def _mostra_riepilogo(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int):
    d = ctx.user_data
    telefono_str     = d.get("telefono") or "—"
    nome_del_str     = d.get("nome_delegante") or "—"
    note_str         = d.get("note") or "—"
    testo = (
        "📋 *Riepilogo*\n\n"
        f"🪪 Nome:            *{d['nome']}*\n"
        f"🪪 Cognome:         *{d['cognome']}*\n"
        f"📅 Decesso:         *{d['data_decesso'].strftime('%d/%m/%Y')}*\n"
        f"📞 Telefono:        *{telefono_str}*\n"
        f"👤 Delegante:       *{nome_del_str}*\n"
        f"📝 Note:            *{note_str}*\n\n"
        "Confermi l'inserimento?"
    )
    tastiera = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Conferma", callback_data="necrologi_aggiungi_conferma"),
            InlineKeyboardButton("❌ Annulla",  callback_data="necrologi_aggiungi_annulla"),
        ]
    ])
    await _edit(ctx, chat_id, testo, tastiera=tastiera)


async def handler_telefono(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    telefono = update.message.text.strip()
    await update.message.delete()

    if not telefono.lstrip("+").isdigit() or len(telefono) < 6:
        await _edit(ctx, update.effective_chat.id,
                    "⚠️ Numero non valido. Inserisci solo cifre (es. 3331234567):\n\n"
                    "Passo 4/6 — Inserisci il *telefono del delegante*:",
                    tastiera=TASTO_TELEFONO)
        return TELEFONO

    ctx.user_data["telefono"] = telefono
    await _edit(ctx, update.effective_chat.id,
                "Passo 5/6 — Inserisci il *nome del delegante*:",
                tastiera=TASTO_SKIP_ANNULLA)
    return NOME_DELEGANTE


async def handler_tel_nessuno(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["telefono"] = None
    ctx.user_data["nome_delegante"] = None
    await _edit(ctx, update.effective_chat.id,
                "Passo 6/6 — Inserisci eventuali *note*:",
                tastiera=TASTO_SKIP_ANNULLA)
    return NOTE

# ── Step 5: nome delegante ────────────────────────────────────────────────────

async def handler_nome_delegante(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()
    ctx.user_data["nome_delegante"] = testo.title() if testo else None
    await _edit(ctx, update.effective_chat.id,
                "Passo 6/6 — Inserisci eventuali *note*:",
                tastiera=TASTO_SKIP_ANNULLA)
    return NOTE


async def handler_salta_nome_delegante(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["nome_delegante"] = None
    await _edit(ctx, update.effective_chat.id,
                "Passo 6/6 — Inserisci eventuali *note*:",
                tastiera=TASTO_SKIP_ANNULLA)
    return NOTE


# ── Step 6: note ──────────────────────────────────────────────────────────────

async def handler_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()
    ctx.user_data["note"] = testo if testo else None
    await _mostra_riepilogo(ctx, update.effective_chat.id)
    return CONFERMA


async def handler_salta_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["note"] = None
    await _mostra_riepilogo(ctx, update.effective_chat.id)
    return CONFERMA

# ── Conferma: salvataggio ─────────────────────────────────────────────────────

async def handler_conferma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    utente = UtenteDAO.get_utente_by_telegram_id(query.from_user.id)
    d = ctx.user_data

    DefuntoDAO().add_defunto(
        nome=d["nome"],
        cognome=d["cognome"],
        data_decesso=d["data_decesso"],
        telefono_delegante=d["telefono"],
        nome_delegante=d.get("nome_delegante"),
        note=d.get("note"),
        aggiunto_da=utente.id,
    )
    ctx.user_data.clear()

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Torna ai defunti", callback_data="necrologi")]
    ])
    await query.edit_message_text("✅ Defunto aggiunto con successo!", reply_markup=tastiera)
    return ConversationHandler.END


# ── Annulla ───────────────────────────────────────────────────────────────────

async def handler_annulla(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Operazione annullata.", show_alert=True)
    ctx.user_data.clear()

    await handler_defunti(update, ctx)
    return ConversationHandler.END


# ── ConversationHandler ───────────────────────────────────────────────────────

conv_aggiungi_defunto = ConversationHandler(
    entry_points=[CallbackQueryHandler(handler_avvia_aggiungi, pattern="^necrologi_aggiungi$")],
    states={
        NOME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, handler_nome)],
        COGNOME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, handler_cognome)],
        DATA_DECESSO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_data_decesso),
            CallbackQueryHandler(handler_data_oggi, pattern="^necrologi_aggiungi_oggi$"),
        ],
        TELEFONO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_telefono),
            CallbackQueryHandler(handler_tel_nessuno, pattern="^necrologi_aggiungi_tel_nessuno$"),
        ],
        NOME_DELEGANTE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_nome_delegante),
            CallbackQueryHandler(handler_salta_nome_delegante, pattern="^necrologi_aggiungi_salta$"),
        ],
        NOTE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_note),
            CallbackQueryHandler(handler_salta_note, pattern="^necrologi_aggiungi_salta$"),
        ],
        CONFERMA: [
            CallbackQueryHandler(handler_conferma, pattern="^necrologi_aggiungi_conferma$"),
            CallbackQueryHandler(handler_annulla,  pattern="^necrologi_aggiungi_annulla$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(handler_annulla, pattern="^necrologi_aggiungi_annulla$")],
    per_message=False,
    per_chat=True,
)