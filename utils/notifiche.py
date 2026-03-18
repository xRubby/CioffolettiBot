"""
utils/notifiche.py — Job giornaliero: notifica le scadenze non completate
"""

import logging
from datetime import date

from telegram.ext import ContextTypes

from config import (
    GIORNI_RINGRAZIAMENTO,
    GIORNI_PRECI,
    GIORNI_TRIGESIMO,
    Stato,
)
from database.DAO.DefuntoDAO import DefuntoDAO
from database.DAO.UtenteDAO import UtenteDAO

logger = logging.getLogger(__name__)

_SCADENZE = [
    ("stato_ringraziamento", GIORNI_RINGRAZIAMENTO, "Ringraziamento", "📬"),
    ("stato_preci",          GIORNI_PRECI,          "Preci",          "🙏"),
    ("stato_trigesimo",      GIORNI_TRIGESIMO,       "Trigesimo",      "📿"),
]


async def job_notifiche_scadenze(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Eseguito ogni giorno a NOTIFICA_ORA:NOTIFICA_MINUTO.
    Per ogni defunto controlla se una scadenza è superata e lo stato non è 'fatto';
    se sì invia un messaggio a tutti gli utenti attivi.
    """
    print("Notifiche inviate")
    oggi = date.today()
    utenti_attivi = UtenteDAO.get_utenti_attivi()

    if not utenti_attivi:
        return
    
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

                for utente in utenti_attivi:
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