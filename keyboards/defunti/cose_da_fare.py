from datetime import date, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.DAO.DefuntoDAO import DefuntoDAO
from database.DAO.AnniversarioDAO import AnniversarioDAO
from config import Stato

PAGINA_SIZE = 5

LEGENDA = (
    f"*Legenda stati:*\n"
    f"🔴 Da fare\n"
    f"🟡 Da confermare\n"
    f"🟢 Confermato\n\n"
    f"*Attività defunti:*\n"
    f"📬 Ringraziamento\n🙏 Preci\n📿 Trigesimo\n\n"
    f"*Attività anniversari:*\n"
    f"📅 Anniversario in scadenza"
)

LEGENDA_ANNIV = (
    f"*Legenda stati:*\n"
    f"🔴 Da fare\n"
    f"🟡 Da confermare\n"
    f"🟢 Confermato"
)


def _anniversari_in_sospeso() -> list:
    return AnniversarioDAO().get_anniversari_in_sospeso(date.today())


# ── Vista principale: defunti + riepilogo anniversari ────────────────────────

async def handler_cose_da_fare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    pagina = int(data.split("_")[-1]) if data.startswith("necrologi_cose_da_fare_p_") else 0
    offset = pagina * PAGINA_SIZE

    dao = DefuntoDAO()
    totale_defunti = dao.conta_defunti_in_sospeso()
    anniversari_sospeso = _anniversari_in_sospeso()

    tastiera_back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Indietro", callback_data="necrologi")]
    ])

    if totale_defunti == 0 and not anniversari_sospeso:
        await query.edit_message_text(
            "✅ *Nessuna attività in sospeso!*\n\nTutti i defunti e gli anniversari sono in regola.",
            parse_mode="Markdown",
            reply_markup=tastiera_back,
        )
        return

    righe = []

    # ── Sezione defunti ───────────────────────────────────────────────────────
    if totale_defunti > 0:
        defunti = dao.get_defunti_in_sospeso_paginati(offset=offset, limit=PAGINA_SIZE)

        for d in defunti:
            icone = []
            if d.stato_ringraziamento in Stato.NON_COMPLETATI:
                icone.append(f"📬{Stato.EMOJI[d.stato_ringraziamento].split()[0]}")
            if d.stato_preci in Stato.NON_COMPLETATI:
                icone.append(f"🙏{Stato.EMOJI[d.stato_preci].split()[0]}")
            if d.stato_trigesimo in Stato.NON_COMPLETATI:
                icone.append(f"📿{Stato.EMOJI[d.stato_trigesimo].split()[0]}")

            label = f"🪦 {d.cognome} {d.nome} — {' '.join(icone)}"
            righe.append([InlineKeyboardButton(label, callback_data=f"necrologi_scheda_{d.id}")])

        n_pagine = -(-totale_defunti // PAGINA_SIZE)
        nav = []
        if pagina > 0:
            if n_pagine >= 3:
                nav.append(InlineKeyboardButton("⏮️", callback_data="necrologi_cose_da_fare_p_0"))
            nav.append(InlineKeyboardButton("◀️ Prec", callback_data=f"necrologi_cose_da_fare_p_{pagina - 1}"))
        if offset + PAGINA_SIZE < totale_defunti:
            nav.append(InlineKeyboardButton("Succ ▶️", callback_data=f"necrologi_cose_da_fare_p_{pagina + 1}"))
            if n_pagine >= 3:
                nav.append(InlineKeyboardButton("⏭️", callback_data=f"necrologi_cose_da_fare_p_{n_pagine - 1}"))
        if nav:
            righe.append(nav)

    # ── Pulsante anniversari ──────────────────────────────────────────────────
    if anniversari_sospeso:
        n = len(anniversari_sospeso)
        righe.append([InlineKeyboardButton(
            f"📅 Anniversari da fare ({n})",
            callback_data="necrologi_anniversari_da_fare_p_0",
        )])

    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data="necrologi")])

    # intestazione
    parti = []
    if totale_defunti:
        parti.append(f"{totale_defunti} defunt{'o' if totale_defunti == 1 else 'i'}")
    if anniversari_sospeso:
        n = len(anniversari_sospeso)
        parti.append(f"{n} anniversar{'io' if n == 1 else 'i'}")

    intestazione = f"📌 *Cose da fare* — {' e '.join(parti)} in sospeso"
    if totale_defunti > 0:
        n_pagine = -(-totale_defunti // PAGINA_SIZE)
        intestazione += f" (pagina {pagina + 1}/{n_pagine})"

    await query.edit_message_text(
        f"{intestazione}\n\n{LEGENDA}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )


# ── Vista dedicata: lista anniversari in sospeso ─────────────────────────────

async def handler_anniversari_da_fare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pagina = int(query.data.split("_")[-1])
    offset = pagina * PAGINA_SIZE

    tutti = _anniversari_in_sospeso()
    totale = len(tutti)
    pagina_items = tutti[offset: offset + PAGINA_SIZE]

    defunti_cache: dict = {}
    for a in pagina_items:
        if a.defunto_id not in defunti_cache:
            defunti_cache[a.defunto_id] = DefuntoDAO().get_defunto(a.defunto_id)

    righe = []
    for a in pagina_items:
        d = defunti_cache.get(a.defunto_id)
        nome_defunto = f"{d.cognome} {d.nome}" if d else f"#{a.defunto_id}"
        stato_emoji = Stato.EMOJI.get(a.stato, a.stato).split()[0]
        label = (
            f"📅{stato_emoji} {AnniversarioDAO.label_numero(a.numero)} "
            f"{nome_defunto} — {a.data.strftime('%d/%m/%Y')}"
        )
        righe.append([InlineKeyboardButton(label, callback_data=f"anniv_scheda_{a.id}")])

    n_pagine = -(-totale // PAGINA_SIZE)
    nav = []
    if pagina > 0:
        if n_pagine >= 3:
            nav.append(InlineKeyboardButton("⏮️", callback_data="necrologi_anniversari_da_fare_p_0"))
        nav.append(InlineKeyboardButton("◀️ Prec", callback_data=f"necrologi_anniversari_da_fare_p_{pagina - 1}"))
    if offset + PAGINA_SIZE < totale:
        nav.append(InlineKeyboardButton("Succ ▶️", callback_data=f"necrologi_anniversari_da_fare_p_{pagina + 1}"))
        if n_pagine >= 3:
            nav.append(InlineKeyboardButton("⏭️", callback_data=f"necrologi_anniversari_da_fare_p_{n_pagine - 1}"))
    if nav:
        righe.append(nav)

    righe.append([InlineKeyboardButton("📌 Cose da fare", callback_data="necrologi_cose_da_fare")])
    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data="necrologi")])
    

    await query.edit_message_text(
        f"📅 *Anniversari in sospeso* — {totale} in totale (pagina {pagina + 1}/{n_pagine})\n\n"
        f"{LEGENDA_ANNIV}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )