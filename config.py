"""
config.py — Configurazione centralizzata del bot Cioffoletti
"""
 
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
 
# ── Bot ──────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN: str = os.environ.get("TELEGRAM_TOKEN", "")
 
# ── Database ─────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
DB_PATH   = BASE_DIR / "cioffoletti.db"
 
# ── Scadenze (giorni dal decesso) ────────────────────────────────────────────
GIORNI_RINGRAZIAMENTO: int = 8
GIORNI_PRECI:          int = 17
GIORNI_TRIGESIMO:      int = 17
 
# ── Job scheduler ────────────────────────────────────────────────────────────
NOTIFICA_ORA:    int = 8
NOTIFICA_MINUTO: int = 0
TIMEZONE:        str = "Europe/Rome"

# ── Stati defunto ────────────────────────────────────────────────────────────
class Stato:
    DA_FARE       = "da_fare"
    DA_CONFERMARE = "da_confermare"
    CONFERMATO    = "confermato"
    FATTO         = "fatto"
 
    TUTTI:           list[str] = [DA_FARE, DA_CONFERMARE, CONFERMATO, FATTO]
    NON_COMPLETATI:  set[str]  = {DA_FARE, DA_CONFERMARE, CONFERMATO}
 
    EMOJI: dict[str, str] = {
        DA_FARE:       "🔴 Da fare",
        DA_CONFERMARE: "🟡 Da confermare",
        CONFERMATO:    "🟢 Confermato",
        FATTO:         "✅ Fatto",
    }