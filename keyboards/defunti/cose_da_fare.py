from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.DAO.DefuntoDAO import DefuntoDAO
from config import Stato

PAGINA_SIZE = 5

LEGENDA = (
    f"*Legenda stati:*\n"
    f"🔴 Da fare\n"
    f"🟡 Da confermare\n"
    f"🟢 Confermato\n\n"
    f"*Attività:*\n"
    f"📬 Ringraziamento\n"
    f"🙏 Preci\n"
    f"📿 Trigesimo"
)


async def handler_cose_da_fare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    pagina = int(data.split("_")[-1]) if data.startswith("necrologi_cose_da_fare_p_") else 0
    offset = pagina * PAGINA_SIZE

    dao = DefuntoDAO()
    totale = dao.conta_defunti_in_sospeso()

    tastiera_back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Indietro", callback_data="necrologi")]
    ])

    if totale == 0:
        await query.edit_message_text(
            "✅ *Nessuna attività in sospeso!*\n\nTutti i defunti hanno le attività completate.",
            parse_mode="Markdown",
            reply_markup=tastiera_back,
        )
        return

    defunti = dao.get_defunti_in_sospeso_paginati(offset=offset, limit=PAGINA_SIZE)

    righe = []
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

    nav = []
    if pagina > 0:
        nav.append(InlineKeyboardButton("◀️ Prec", callback_data=f"necrologi_cose_da_fare_p_{pagina - 1}"))
    if offset + PAGINA_SIZE < totale:
        nav.append(InlineKeyboardButton("Succ ▶️", callback_data=f"necrologi_cose_da_fare_p_{pagina + 1}"))
    if nav:
        righe.append(nav)

    righe.append([InlineKeyboardButton("🔙 Indietro", callback_data="necrologi")])

    await query.edit_message_text(
        f"📌 *Cose da fare* — {totale} defunt{'o' if totale == 1 else 'i'} con attività in sospeso "
        f"(pagina {pagina + 1}/{-(-totale // PAGINA_SIZE)})\n\n"
        f"{LEGENDA}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(righe),
    )