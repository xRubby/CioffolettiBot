"""
utils/notifiche.py — Job giornaliero: notifica le scadenze non completate
"""

import logging
from datetime import date, timedelta

from telegram.ext import ContextTypes

from config import (
    GIORNI_RINGRAZIAMENTO,
    GIORNI_PRECI,
    GIORNI_TRIGESIMO,
    Stato,
)
from database.DAO.DefuntoDAO import DefuntoDAO
from database.DAO.UtenteDAO import UtenteDAO
from database.DAO.AnniversarioDAO import AnniversarioDAO

logger = logging.getLogger(__name__)

_SCADENZE = [
    ("stato_ringraziamento", GIORNI_RINGRAZIAMENTO, "Ringraziamento", "📬"),
    ("stato_preci",          GIORNI_PRECI,          "Preci",          "🙏"),
    ("stato_trigesimo",      GIORNI_TRIGESIMO,       "Trigesimo",      "📿"),
]


async def job_notifiche_scadenze(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    oggi = date.today()
    utenti_attivi = UtenteDAO.get_utenti_attivi()

    if not utenti_attivi:
        return

    # ── Ringraziamento / Preci / Trigesimo ────────────────────────────────────
    defunti = DefuntoDAO().get_tutti_defunti()

    for d in defunti:
        giorni_trascorsi = (oggi - d.data_decesso).days

        for campo, soglia, etichetta, emoji in _SCADENZE:
            stato_attuale = getattr(d, campo)

            if giorni_trascorsi >= soglia and stato_attuale not in (Stato.FATTO, Stato.NON_FARE):
                stato_label = Stato.EMOJI.get(stato_attuale, stato_attuale)
                testo = (
                    f"⚠️ <b>Scadenza superata</b>\n\n"
                    f"🪦 <b>{d.cognome} {d.nome}</b>\n"
                    f"📅 Deceduto/a il {d.data_decesso.strftime('%d/%m/%Y')} "
                    f"({giorni_trascorsi} giorni fa)\n\n"
                    f"{emoji} <b>{etichetta}:</b> {stato_label}"
                )
                await _invia_a_tutti(ctx, utenti_attivi, testo)

    # ── Anniversari ───────────────────────────────────────────────────────────
    anniversari = AnniversarioDAO().get_tutti()

    for a in anniversari:
        if a.stato in (Stato.FATTO, Stato.NON_FARE):
            continue

        # data di riferimento: affissione - 3 giorni, oppure la data stessa
        if a.data_affissione:
            data_notifica = a.data_affissione - timedelta(days=3)
        else:
            data_notifica = a.data

        if oggi < data_notifica:
            continue

        # recupera il defunto per nome e cognome
        d = DefuntoDAO().get_defunto(a.defunto_id)
        if not d:
            continue

        stato_label     = Stato.EMOJI.get(a.stato, a.stato)
        descrizione_str = f"\n📝 {a.descrizione}" if a.descrizione else ""
        affissione_str  = (
            f"\n📌 Affissione: {a.data_affissione.strftime('%d/%m/%Y')}"
            if a.data_affissione else ""
        )

        testo = (
            f"📅 <b>{AnniversarioDAO.label_numero(a.numero).capitalize()} in scadenza</b>\n\n"
            f"🪦 <b>{d.cognome} {d.nome}</b>\n"
            f"🗓 Data: {a.data.strftime('%d/%m/%Y')}"
            f"{affissione_str}"
            f"{descrizione_str}\n\n"
            f"🔵 <b>Stato:</b> {stato_label}"
        )
        await _invia_a_tutti(ctx, utenti_attivi, testo)


# ── Helper interno ────────────────────────────────────────────────────────────

async def _invia_a_tutti(ctx, utenti, testo: str) -> None:
    for utente in utenti:
        try:
            await ctx.bot.send_message(
                chat_id=utente.telegram_user_id,
                text=testo,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(
                "Impossibile inviare notifica a %s: %s",
                utente.telegram_user_id, e,
            )