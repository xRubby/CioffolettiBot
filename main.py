from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, JobQueue
import logging
from config import TELEGRAM_TOKEN
from database.Connessione import db_connection

from keyboards.main_menu import cmd_start, handler_menu_principale
from keyboards.impostazioni.settings_menu import handler_impostazioni, handler_profilo
from keyboards.impostazioni.admin_settings_menu import (
    conv_ricerca,
    handler_admin, handler_pagina_prec, handler_pagina_succ,
    handler_utente, handler_toggle_admin, handler_toggle_stato,
)
from keyboards.defunti.handle_defunti import handler_defunti
from keyboards.defunti.aggiungi_defunto import conv_aggiungi_defunto
from keyboards.defunti.lista_defunti import (
    conv_ricerca_defunto,
    handler_lista_defunti,
    handler_scheda_defunto,
)
from keyboards.defunti.modifica_defunto import (
    conv_modifica_defunto,
)
from keyboards.defunti.cose_da_fare import handler_cose_da_fare, handler_anniversari_da_fare

from keyboards.defunti.anniversari import (          
    conv_aggiungi_anniversario,
    conv_modifica_anniversario,
    handler_lista_anniversari,
    handler_scheda_anniversario,
    handler_cambia_stato,
    handler_salva_stato,
    handler_elimina_chiedi,
    handler_elimina_conferma,
)

from utils.guards import gate_necrologi, gate_admin

from zoneinfo import ZoneInfo
from config import NOTIFICA_ORA, NOTIFICA_MINUTO, TIMEZONE
from utils.notifiche import job_notifiche_scadenze
import datetime

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Imposta la variabile d'ambiente TELEGRAM_TOKEN")

    db_connection.init_schema()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # ── Job scheduler ─────────────────────────────
    job_queue: JobQueue = app.job_queue
    job_queue.run_daily(
        job_notifiche_scadenze,
        time=datetime.time(
            hour=NOTIFICA_ORA,
            minute=NOTIFICA_MINUTO,
            tzinfo=ZoneInfo(TIMEZONE),
        ),
        name="notifiche_scadenze",
        job_kwargs={"misfire_grace_time": 60},
    )

    app.add_handler(gate_necrologi, group=-1)
    app.add_handler(gate_admin, group=-1)

    app.add_handler(CommandHandler("start", cmd_start))

    # ── Defunti ───────────────────────────────────────────────────────────────
    app.add_handler(conv_ricerca_defunto)
    app.add_handler(conv_aggiungi_defunto)
    app.add_handler(conv_modifica_defunto)

    app.add_handler(CallbackQueryHandler(handler_defunti,        pattern="^necrologi$"))
    app.add_handler(CallbackQueryHandler(handler_lista_defunti,  pattern=r"^necrologi_lista(_p_\d+)?$"))
    app.add_handler(CallbackQueryHandler(handler_scheda_defunto, pattern=r"^necrologi_scheda_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_cose_da_fare,        pattern=r"^necrologi_cose_da_fare(_p_\d+)?$"))
    app.add_handler(CallbackQueryHandler(handler_anniversari_da_fare, pattern=r"^necrologi_anniversari_da_fare_p_\d+$"))
    
    # ── Anniversari ───────────────────────────────────────────────────────────
    app.add_handler(conv_aggiungi_anniversario)
    app.add_handler(conv_modifica_anniversario)

    app.add_handler(CallbackQueryHandler(handler_lista_anniversari, pattern=r"^anniv_lista_(p_\d+_)?\d+$"))
    app.add_handler(CallbackQueryHandler(handler_scheda_anniversario, pattern=r"^anniv_scheda_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_cambia_stato,        pattern=r"^anniv_cambia_stato_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_salva_stato,         pattern=r"^anniv_stato_.+_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_elimina_chiedi,      pattern=r"^anniv_elimina_chiedi_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_elimina_conferma,    pattern=r"^anniv_elimina_conferma_\d+$"))

    # ── Impostazioni ──────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handler_impostazioni, pattern="^impostazioni$"))
    app.add_handler(CallbackQueryHandler(handler_profilo,      pattern="^profilo$"))

    app.add_handler(conv_ricerca)

    app.add_handler(CallbackQueryHandler(handler_admin,        pattern="^impostazioni_admin$"))
    app.add_handler(CallbackQueryHandler(handler_pagina_prec,  pattern="^impostazioni_admin_pagina_prec$"))
    app.add_handler(CallbackQueryHandler(handler_pagina_succ,  pattern="^impostazioni_admin_pagina_succ$"))
    app.add_handler(CallbackQueryHandler(handler_utente,       pattern=r"^impostazioni_admin_utente_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_toggle_admin, pattern=r"^impostazioni_admin_toggle_admin_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_toggle_stato, pattern=r"^impostazioni_admin_toggle_stato_\d+$"))
    app.add_handler(CallbackQueryHandler(handler_menu_principale, pattern="^menu_principale$"))

    logger.info("Bot Cioffoletti avviato.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()