from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from datetime import date

from database.DAO.AnniversarioDAO import AnniversarioDAO
from database.DAO.DefuntoDAO import DefuntoDAO
from config import Stato

# ── Stati conversazione ───────────────────────────────────────────────────────
MENU, ATTESA_VALORE = range(2)

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _edit(ctx, chat_id: int, testo: str, tastiera=None, parse_mode="Markdown"):
    await ctx.bot.edit_message_text(
        chat_id=chat_id,
        message_id=ctx.user_data["anniv_msg_id"],
        text=testo,
        parse_mode=parse_mode,
        reply_markup=tastiera,
    )


def _tastiera_annulla(anniversario_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Indietro", callback_data=f"anniv_scheda_{anniversario_id}")]
    ])


def _tastiera_stato(anniversario_id: int) -> InlineKeyboardMarkup:
    righe = [
        [InlineKeyboardButton(label, callback_data=f"anniv_stato_{stato}_{anniversario_id}")]
        for stato, label in Stato.EMOJI.items()
    ]
    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data=f"anniv_scheda_{anniversario_id}")])
    return InlineKeyboardMarkup(righe)


# ── Lista anniversari ─────────────────────────────────────────────────────────

PAGINA_SIZE = 5

async def handler_lista_anniversari(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("anniv_lista_p_"):
        # pattern: anniv_lista_p_{pagina}_{defunto_id}
        parti = data.split("_")
        pagina = int(parti[3])
        defunto_id = int(parti[4])
    else:
        # pattern: anniv_lista_{defunto_id}
        defunto_id = int(data.split("_")[-1])
        pagina = 0

    ctx.user_data["anniv_defunto_id"] = defunto_id
    ctx.user_data["anniv_msg_id"] = query.message.message_id
    ctx.user_data["anniv_pagina"] = pagina

    dao = AnniversarioDAO()
    totale = dao.conta_by_defunto(defunto_id)
    offset = pagina * PAGINA_SIZE
    anniversari = dao.get_by_defunto_paginati(defunto_id, offset=offset, limit=PAGINA_SIZE)

    d = DefuntoDAO().get_defunto(defunto_id)

    ctx.user_data["anniv_defunto_nome"]    = d.nome
    ctx.user_data["anniv_defunto_cognome"] = d.cognome

    righe = []

    for a in anniversari:
        stato_emoji = Stato.EMOJI.get(a.stato, a.stato).split()[0]
        label = f"{stato_emoji} {AnniversarioDAO.label_numero(a.numero)} — {a.data.strftime('%d/%m/%Y')}"
        if a.descrizione:
            label += f" · {a.descrizione[:25]}"
        righe.append([InlineKeyboardButton(label, callback_data=f"anniv_scheda_{a.id}")])

    n_pagine = -(-totale // PAGINA_SIZE)
    nav = []
    if pagina > 0:
        if n_pagine >= 3:
            nav.append(InlineKeyboardButton("⏮️", callback_data=f"anniv_lista_p_0_{defunto_id}"))
        nav.append(InlineKeyboardButton("◀️ Prec", callback_data=f"anniv_lista_p_{pagina - 1}_{defunto_id}"))
    if offset + PAGINA_SIZE < totale:
        nav.append(InlineKeyboardButton("Succ ▶️", callback_data=f"anniv_lista_p_{pagina + 1}_{defunto_id}"))
        if n_pagine >= 3:
            nav.append(InlineKeyboardButton("⏭️", callback_data=f"anniv_lista_p_{n_pagine - 1}_{defunto_id}"))
    if nav:
        righe.append(nav)

    righe.append([InlineKeyboardButton("➕ Aggiungi anniversario", callback_data=f"anniv_aggiungi_{defunto_id}")])
    righe.append([InlineKeyboardButton("🔙 Scheda defunto", callback_data=f"necrologi_scheda_{defunto_id}")])

    testo = (
        f"📅 *Anniversari — {d.cognome} {d.nome}*\n\n"
        + (f"{totale} anniversar{'io' if totale == 1 else 'i'} presenti "
           f"(pagina {pagina + 1}/{n_pagine})"
           if totale else "Nessun anniversario presente.")
    )

    await ctx.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=query.message.message_id,
        text=testo,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )


# ── Scheda singolo anniversario ───────────────────────────────────────────────

async def handler_scheda_anniversario(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    anniversario_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_msg_id"] = query.message.message_id

    a = AnniversarioDAO().get_anniversario(anniversario_id)
    if not a:
        await query.answer("Anniversario non trovato.", show_alert=True)
        return

    await _mostra_scheda(ctx, update.effective_chat.id, anniversario_id)


# ── Cambia stato ──────────────────────────────────────────────────────────────

async def handler_cambia_stato(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    anniversario_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_msg_id"] = query.message.message_id

    a = AnniversarioDAO().get_anniversario(anniversario_id)
    await query.edit_message_text(
        "🏷️ Scegli il nuovo stato:",
        reply_markup=_tastiera_stato(anniversario_id),
    )


async def handler_salva_stato(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Callback: anniv_stato_{stato}_{anniversario_id}"""
    query = update.callback_query
    await query.answer()

    parti = query.data.split("_")
    anniversario_id = int(parti[-1])
    stato = "_".join(parti[2:-1])

    AnniversarioDAO().aggiorna_stato(anniversario_id, stato)

    query.data = f"anniv_scheda_{anniversario_id}"
    await handler_scheda_anniversario(update, ctx)


# ── Modifica anniversario ─────────────────────────────────────────────────────

async def handler_menu_modifica(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    anniversario_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_modifica_id"] = anniversario_id
    ctx.user_data["anniv_msg_id"] = query.message.message_id

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Data", callback_data=f"anniv_mod_data_{anniversario_id}"),
         InlineKeyboardButton("📌 Data affissione", callback_data=f"anniv_mod_affissione_{anniversario_id}")],
        [InlineKeyboardButton("📝 Descrizione", callback_data=f"anniv_mod_descrizione_{anniversario_id}")],
        [InlineKeyboardButton("🔙 Indietro", callback_data=f"anniv_scheda_{anniversario_id}")],
    ])
    await query.edit_message_text(
        "✏️ *Modifica anniversario* — scegli il campo:",
        parse_mode="Markdown",
        reply_markup=tastiera,
    )
    return MENU


async def handler_mod_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anniversario_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_modifica_id"] = anniversario_id
    ctx.user_data["anniv_campo"] = "data"
    await _edit(ctx, update.effective_chat.id,
                "📅 *Modifica Data*\n\nFormato: *GG/MM/AAAA*",
                tastiera=_tastiera_annulla(anniversario_id))
    return ATTESA_VALORE


async def handler_mod_affissione(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anniversario_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_modifica_id"] = anniversario_id
    ctx.user_data["anniv_campo"] = "data_affissione"
    await _edit(ctx, update.effective_chat.id,
                "📌 *Modifica Data affissione*\n\nFormato: *GG/MM/AAAA*, oppure `nessuno` per rimuoverla:",
                tastiera=_tastiera_annulla(anniversario_id))
    return ATTESA_VALORE


async def handler_mod_descrizione(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anniversario_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_modifica_id"] = anniversario_id
    ctx.user_data["anniv_campo"] = "descrizione"
    await _edit(ctx, update.effective_chat.id,
                "📝 *Modifica Descrizione*\n\nInvia il testo, oppure `nessuno` per rimuoverla:",
                tastiera=_tastiera_annulla(anniversario_id))
    return ATTESA_VALORE


# ── Helpers (aggiunta) ────────────────────────────────────────────────────────

async def _mostra_scheda(ctx, chat_id: int, anniversario_id: int, prefisso: str = ""):
    a = AnniversarioDAO().get_anniversario(anniversario_id)

    nome    = ctx.user_data.get("anniv_defunto_nome", "")
    cognome = ctx.user_data.get("anniv_defunto_cognome", "")

    if not nome and not cognome:
        d = DefuntoDAO().get_defunto(a.defunto_id)
        nome    = d.nome
        cognome = d.cognome

    affissione_str  = a.data_affissione.strftime('%d/%m/%Y') if a.data_affissione else "—"
    descrizione_str = a.descrizione if a.descrizione else "—"

    testo = (
        f"{prefisso}"
        f"📅 <b>{AnniversarioDAO.label_numero(a.numero).capitalize()}</b>\n\n"
        f"🪦 <b>{nome} {cognome}</b>\n\n"
        f"🗓 <b>Data:</b> {a.data.strftime('%d/%m/%Y')}\n"
        f"📌 <b>Data affissione:</b> {affissione_str}\n"
        f"📝 <b>Descrizione:</b> {descrizione_str}\n"
        f"🏷️ <b>Stato:</b> {Stato.EMOJI.get(a.stato, a.stato)}\n"
    )

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Modifica",       callback_data=f"anniv_modifica_{anniversario_id}"),
        InlineKeyboardButton("🏷️ Cambia stato",   callback_data=f"anniv_cambia_stato_{anniversario_id}")],
        [InlineKeyboardButton("🗑️ Elimina",        callback_data=f"anniv_elimina_chiedi_{anniversario_id}")],
        [InlineKeyboardButton("🔙 Lista anniversari", callback_data=f"anniv_lista_{a.defunto_id}")],
    ])

    await ctx.bot.edit_message_text(
        chat_id=chat_id,
        message_id=ctx.user_data["anniv_msg_id"],
        text=testo,
        parse_mode="HTML",
        reply_markup=tastiera,
    )

async def handler_ricevi_valore(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()

    anniversario_id = ctx.user_data["anniv_modifica_id"]
    campo           = ctx.user_data["anniv_campo"]
    chat_id         = update.effective_chat.id
    dao             = AnniversarioDAO()

    if campo == "data":
        try:
            g, m, an = testo.split("/")
            data = date(int(an), int(m), int(g))
        except (ValueError, TypeError):
            await _edit(ctx, chat_id,
                        "⚠️ Formato non valido. Usa *GG/MM/AAAA*:",
                        tastiera=_tastiera_annulla(anniversario_id))
            return ATTESA_VALORE
        dao.aggiorna_campo(anniversario_id, "data", data.isoformat())

    elif campo == "data_affissione":
        if testo.lower() == "nessuno":
            dao.aggiorna_campo(anniversario_id, "data_affissione", None)
        else:
            try:
                g, m, an = testo.split("/")
                data = date(int(an), int(m), int(g))
            except (ValueError, TypeError):
                await _edit(ctx, chat_id,
                            "⚠️ Formato non valido. Usa *GG/MM/AAAA* o `nessuno`:",
                            tastiera=_tastiera_annulla(anniversario_id))
                return ATTESA_VALORE
            dao.aggiorna_campo(anniversario_id, "data_affissione", data.isoformat())

    elif campo == "descrizione":
        dao.aggiorna_campo(anniversario_id, "descrizione",
                           None if testo.lower() == "nessuno" else testo)

    await _mostra_scheda(ctx, chat_id, anniversario_id, prefisso="✅ <b>Salvato!</b>\n\n")
    return MENU

# ── Elimina anniversario ──────────────────────────────────────────────────────

async def handler_elimina_chiedi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    anniversario_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_msg_id"] = query.message.message_id
    a = AnniversarioDAO().get_anniversario(anniversario_id)

    tastiera = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sì, elimina", callback_data=f"anniv_elimina_conferma_{anniversario_id}"),
            InlineKeyboardButton("❌ No, annulla", callback_data=f"anniv_scheda_{anniversario_id}"),
        ]
    ])
    await query.edit_message_text(
        f"🗑️ *Eliminare questo anniversario?*\n\n"
        f"📅 {AnniversarioDAO.label_numero(a.numero)} — {a.data.strftime('%d/%m/%Y')}"
        + (f"\n📝 {a.descrizione}" if a.descrizione else "")
        + "\n\n⚠️ L'operazione è *irreversibile*.",
        parse_mode="Markdown",
        reply_markup=tastiera,
    )
    return MENU


async def handler_elimina_conferma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    anniversario_id = int(query.data.split("_")[-1])
    a = AnniversarioDAO().get_anniversario(anniversario_id)
    defunto_id = a.defunto_id
    AnniversarioDAO().elimina_anniversario(anniversario_id)

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Lista anniversari", callback_data=f"anniv_lista_{defunto_id}")]
    ])
    await query.edit_message_text(
        "✅ *Anniversario eliminato.*",
        parse_mode="Markdown",
        reply_markup=tastiera,
    )
    return ConversationHandler.END


# ── Aggiungi anniversario ─────────────────────────────────────────────────────

AGGIUNGI_DATA, AGGIUNGI_AFFISSIONE, AGGIUNGI_DESCRIZIONE, AGGIUNGI_CONFERMA = range(10, 14)

TASTO_SALTA_ANNULLA_DEF = lambda defunto_id: InlineKeyboardMarkup([
    [InlineKeyboardButton("⏭ Salta", callback_data=f"anniv_aggiungi_salta_{defunto_id}")],
    [InlineKeyboardButton("❌ Annulla", callback_data=f"anniv_lista_{defunto_id}")],
])


async def handler_avvia_aggiungi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["anniv_defunto_id"] = defunto_id
    ctx.user_data["anniv_msg_id"] = query.message.message_id
    ctx.user_data.pop("new_anniv", None)

    await query.edit_message_text(
        "➕ *Nuovo anniversario*\n\nPasso 1/3 — Inserisci la *data* (GG/MM/AAAA):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Annulla", callback_data=f"anniv_lista_{defunto_id}")]
        ]),
    )
    return AGGIUNGI_DATA


async def handler_aggiungi_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()
    defunto_id = ctx.user_data["anniv_defunto_id"]

    try:
        g, m, a = testo.split("/")
        data = date(int(a), int(m), int(g))
    except (ValueError, TypeError):
        await _edit(ctx, update.effective_chat.id,
                    "⚠️ Formato non valido. Usa *GG/MM/AAAA*:\n\nPasso 1/3 — *Data:*",
                    tastiera=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annulla", callback_data=f"anniv_lista_{defunto_id}")]]))
        return AGGIUNGI_DATA

    ctx.user_data.setdefault("new_anniv", {})["data"] = data
    await _edit(ctx, update.effective_chat.id,
                "Passo 2/3 — Inserisci la *data di affissione* (GG/MM/AAAA):",
                tastiera=TASTO_SALTA_ANNULLA_DEF(defunto_id))
    return AGGIUNGI_AFFISSIONE


async def handler_aggiungi_affissione(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()
    defunto_id = ctx.user_data["anniv_defunto_id"]

    try:
        g, m, a = testo.split("/")
        data = date(int(a), int(m), int(g))
    except (ValueError, TypeError):
        await _edit(ctx, update.effective_chat.id,
                    "⚠️ Formato non valido. Usa *GG/MM/AAAA* o salta:\n\nPasso 2/3 — *Data affissione:*",
                    tastiera=TASTO_SALTA_ANNULLA_DEF(defunto_id))
        return AGGIUNGI_AFFISSIONE

    ctx.user_data["new_anniv"]["data_affissione"] = data
    await _edit(ctx, update.effective_chat.id,
                "Passo 3/3 — Inserisci una *descrizione* (opzionale):",
                tastiera=TASTO_SALTA_ANNULLA_DEF(defunto_id))
    return AGGIUNGI_DESCRIZIONE


async def handler_salta_affissione(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    defunto_id = int(query.data.split("_")[-1])
    ctx.user_data["new_anniv"]["data_affissione"] = None
    await _edit(ctx, update.effective_chat.id,
                "Passo 3/3 — Inserisci una *descrizione* (opzionale):",
                tastiera=TASTO_SALTA_ANNULLA_DEF(defunto_id))
    return AGGIUNGI_DESCRIZIONE


async def handler_aggiungi_descrizione(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip()
    await update.message.delete()
    ctx.user_data["new_anniv"]["descrizione"] = testo or None
    await _mostra_riepilogo_aggiungi(ctx, update.effective_chat.id)
    return AGGIUNGI_CONFERMA


async def handler_salta_descrizione(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["new_anniv"]["descrizione"] = None
    await _mostra_riepilogo_aggiungi(ctx, update.effective_chat.id)
    return AGGIUNGI_CONFERMA


async def _mostra_riepilogo_aggiungi(ctx, chat_id: int):
    d = ctx.user_data["new_anniv"]
    affissione_str = d.get("data_affissione").strftime('%d/%m/%Y') if d.get("data_affissione") else "—"
    descrizione_str = d.get("descrizione") or "—"

    testo = (
        "📋 *Riepilogo anniversario*\n\n"
        f"📅 Data:           *{d['data'].strftime('%d/%m/%Y')}*\n"
        f"📌 Affissione:     *{affissione_str}*\n"
        f"📝 Descrizione:    *{descrizione_str}*\n\n"
        "Confermi l'inserimento?"
    )
    defunto_id = ctx.user_data["anniv_defunto_id"]
    tastiera = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Conferma", callback_data="anniv_aggiungi_conferma"),
            InlineKeyboardButton("❌ Annulla",  callback_data=f"anniv_lista_{defunto_id}"),
        ]
    ])
    await _edit(ctx, chat_id, testo, tastiera=tastiera)


async def handler_aggiungi_conferma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    d = ctx.user_data["new_anniv"]
    defunto_id = ctx.user_data["anniv_defunto_id"]

    AnniversarioDAO().add_anniversario(
        defunto_id=defunto_id,
        data=d["data"],
        data_affissione=d.get("data_affissione"),
        descrizione=d.get("descrizione"),
    )
    ctx.user_data.pop("new_anniv", None)

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Lista anniversari", callback_data=f"anniv_lista_{defunto_id}")]
    ])
    await query.edit_message_text("✅ *Anniversario aggiunto con successo!*",
                                  parse_mode="Markdown", reply_markup=tastiera)
    return ConversationHandler.END

async def handler_annulla_aggiungi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("new_anniv", None)
    ctx.user_data.pop("anniv_defunto_id", None)
    await handler_lista_anniversari(update, ctx)
    return ConversationHandler.END

async def handler_annulla_modifica(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await handler_scheda_anniversario(update, ctx)
    return ConversationHandler.END


# ── ConversationHandler modifica ─────────────────────────────────────────────

conv_modifica_anniversario = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handler_menu_modifica, pattern=r"^anniv_modifica_\d+$"),
    ],
    states={
        MENU: [
            CallbackQueryHandler(handler_mod_data,        pattern=r"^anniv_mod_data_\d+$"),
            CallbackQueryHandler(handler_mod_affissione,  pattern=r"^anniv_mod_affissione_\d+$"),
            CallbackQueryHandler(handler_mod_descrizione, pattern=r"^anniv_mod_descrizione_\d+$"),
            CallbackQueryHandler(handler_elimina_chiedi,  pattern=r"^anniv_elimina_chiedi_\d+$"),
            CallbackQueryHandler(handler_elimina_conferma,pattern=r"^anniv_elimina_conferma_\d+$"),
            CallbackQueryHandler(handler_menu_modifica,   pattern=r"^anniv_modifica_\d+$"),
            CallbackQueryHandler(handler_annulla_modifica, pattern=r"^anniv_scheda_\d+$"),
        ],
        ATTESA_VALORE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_ricevi_valore),
            CallbackQueryHandler(handler_menu_modifica,   pattern=r"^anniv_modifica_\d+$"),
            CallbackQueryHandler(handler_annulla_modifica, pattern=r"^anniv_scheda_\d+$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handler_menu_modifica, pattern=r"^anniv_modifica_\d+$"),
    ],
    per_message=False,
    per_chat=True,
)

# ── ConversationHandler aggiungi ──────────────────────────────────────────────

conv_aggiungi_anniversario = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handler_avvia_aggiungi, pattern=r"^anniv_aggiungi_\d+$"),
    ],
    states={
        AGGIUNGI_DATA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_aggiungi_data),
            CallbackQueryHandler(handler_annulla_aggiungi, pattern=r"^anniv_lista_\d+$"),
        ],
        AGGIUNGI_AFFISSIONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_aggiungi_affissione),
            CallbackQueryHandler(handler_salta_affissione, pattern=r"^anniv_aggiungi_salta_\d+$"),
            CallbackQueryHandler(handler_annulla_aggiungi, pattern=r"^anniv_lista_\d+$"),
        ],
        AGGIUNGI_DESCRIZIONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_aggiungi_descrizione),
            CallbackQueryHandler(handler_salta_descrizione, pattern=r"^anniv_aggiungi_salta_\d+$"),
            CallbackQueryHandler(handler_annulla_aggiungi, pattern=r"^anniv_lista_\d+$"),
        ],
        AGGIUNGI_CONFERMA: [
            CallbackQueryHandler(handler_aggiungi_conferma, pattern=r"^anniv_aggiungi_conferma$"),
            CallbackQueryHandler(handler_annulla_aggiungi, pattern=r"^anniv_lista_\d+$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handler_annulla_aggiungi, pattern=r"^anniv_lista_\d+$"),
    ],
    per_message=False,
    per_chat=True,
)