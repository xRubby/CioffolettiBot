"""
database/connection.py — Gestione connessione SQLite
"""
 
import sqlite3
from contextlib import contextmanager
from config import DB_PATH
 
 
class DatabaseConnection:
    """Singleton che gestisce la connessione al database SQLite."""
 
    _instance: "DatabaseConnection | None" = None
 
    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
 
    # ── Connessione grezza ───────────────────────────────────────────────────
    def get_connection(self) -> sqlite3.Connection:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con
 
    # ── Context manager ─────────────────────────
    @contextmanager
    def connect(self):
        con = self.get_connection()
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
 
    # ── DDL ──────────────────────────────────────────────────────────────────
    def init_schema(self) -> None:
        """Crea le tabelle se non esistono."""
        with self.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS utenti (
                    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id      INTEGER NOT NULL UNIQUE,
                    telegram_username      TEXT,
                    is_admin              INTEGER NOT NULL DEFAULT 0 CHECK(is_admin IN (0,1)),
                    is_active             INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1))
                );
                              
                CREATE TABLE IF NOT EXISTS defunti (
                    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome                  TEXT    NOT NULL,
                    cognome               TEXT    NOT NULL,
                    data_decesso          TEXT    NOT NULL,
                    telefono_delegante    TEXT    NOT NULL,
                    stato_ringraziamento  TEXT    NOT NULL DEFAULT 'da_fare',
                    stato_preci           TEXT    NOT NULL DEFAULT 'da_fare',
                    stato_trigesimo       TEXT    NOT NULL DEFAULT 'da_fare',
                    creato_il             TEXT    NOT NULL DEFAULT (date('now')),
                    aggiunto_da           INTEGER NOT NULL,

                    FOREIGN KEY (aggiunto_da) REFERENCES utenti(id)
                );
            """)
 
 
# Istanza globale pronta all'uso
db_connection = DatabaseConnection()