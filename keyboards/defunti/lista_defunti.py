from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.DAO.DefuntoDAO import DefuntoDAO
from database.DAO.UtenteDAO import UtenteDAO
from config import Stato

PAGINA_SIZE = 5


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

    tutti = DefuntoDAO().get_tutti_defunti()
    totale = len(tutti)
    offset = pagina * PAGINA_SIZE
    defunti_pagina = tutti[offset: offset + PAGINA_SIZE]

    if not defunti_pagina and pagina == 0:
        tastiera = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Aggiungi defunto", callback_data="necrologi_aggiungi")],
            [InlineKeyboardButton("🔙 Indietro", callback_data="defunti")],
        ])
        await query.edit_message_text(
            "📋 *Lista defunti*\n\nNessun defunto presente.",
            parse_mode="Markdown",
            reply_markup=tastiera,
        )
        return

    righe = []
    for d in defunti_pagina:
        label = f"🪦 {d.cognome} {d.nome} — {d.data_decesso.strftime('%d/%m/%Y')}"
        righe.append([InlineKeyboardButton(label, callback_data=f"necrologi_scheda_{d.id}")])

    nav = []
    if pagina > 0:
        nav.append(InlineKeyboardButton("◀️ Prec", callback_data=f"necrologi_lista_p_{pagina - 1}"))
    if offset + PAGINA_SIZE < totale:
        nav.append(InlineKeyboardButton("Succ ▶️", callback_data=f"necrologi_lista_p_{pagina + 1}"))
    if nav:
        righe.append(nav)

    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data="defunti")])

    await query.edit_message_text(
        f"📋 *Lista defunti* — pagina {pagina + 1} ({totale} totali)",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
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

    testo = (
        f"🪦 <b>{d.cognome} {d.nome}</b>\n\n"
        f"📅 <b>Data decesso:</b> {d.data_decesso.strftime('%d/%m/%Y')}\n"
        f"📞 <b>Telefono delegante:</b> {telefono_str}\n"
        f"🗓 <b>Inserito il:</b> {d.creato_il.strftime('%d/%m/%Y')}\n"
        f"👤 <b>Aggiunto da:</b> {aggiunto_da_str}\n\n"
        f"📬 <b>Ringraziamento:</b> {Stato.EMOJI[d.stato_ringraziamento]}\n"
        f"🙏 <b>Preci:</b> {Stato.EMOJI[d.stato_preci]}\n"
        f"📿 <b>Trigesimo:</b> {Stato.EMOJI[d.stato_trigesimo]}\n"
    )

    pagina = ctx.user_data.get("lista_defunti_pagina", 0)

    tastiera = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Modifica informazioni", callback_data=f"necrologi_modifica_{defunto_id}")],
        [InlineKeyboardButton("🔙 Lista defunti", callback_data=f"necrologi_lista_p_{pagina}")],
    ])

    await query.edit_message_text(testo, parse_mode="HTML", reply_markup=tastiera)