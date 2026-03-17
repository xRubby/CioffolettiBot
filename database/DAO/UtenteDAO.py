from database.Entity.Utente import Utente
from database.Connessione import db_connection


class UtenteDAO:

    @staticmethod
    def aggiungi_utente(telegram_user_id: int, username: str | None, is_admin: bool = False, is_active: bool = False) -> None:
        with db_connection.connect() as con:
            con.execute("""INSERT INTO utenti (telegram_user_id, telegram_username, is_admin, is_active) VALUES (?, ?, ?, ?)""",
                (telegram_user_id, username, int(is_admin), int(is_active)))

    @staticmethod
    def rimuovi_utente(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("""UPDATE utenti SET is_active = 0 WHERE id = ?""", (utente_id,))
    
    @staticmethod
    def riattiva_utente(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("""UPDATE utenti SET is_active = 1 WHERE id = ?""",(utente_id,))
    
    @staticmethod
    def rendi_admin(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("UPDATE utenti SET is_admin = 1 WHERE id = ?", (utente_id,))

    @staticmethod
    def disattiva_admin(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("UPDATE utenti SET is_admin = 0 WHERE id = ?", (utente_id,))

    @staticmethod
    def get_utenti() -> list[Utente]:
        with db_connection.connect() as con:
            rows = con.execute("SELECT * FROM utenti").fetchall()
        return [Utente(**row) for row in rows]
    
    @staticmethod
    def get_utente(utente_id: int) -> Utente | None:
        with db_connection.connect() as con:
            row = con.execute("SELECT * FROM utenti WHERE id = ?", (utente_id,)).fetchone()
        return Utente(**row) if row else None
    
    @staticmethod
    def conta_utenti() -> int:
        with db_connection.connect() as con:
            row = con.execute("SELECT COUNT(*) FROM utenti").fetchone()
            return row[0]

    @staticmethod
    def get_utente_by_telegram_id(telegram_user_id: int) -> Utente | None:
        with db_connection.connect() as con:
            row = con.execute("SELECT * FROM utenti WHERE telegram_user_id = ?", (telegram_user_id,)).fetchone()
            return Utente(**row) if row else None
        
    @staticmethod
    def get_utenti_paginati(offset: int, limit: int = 5) -> list[Utente]:
        with db_connection.connect() as con:
            rows = con.execute(
                "SELECT * FROM utenti LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
            return [Utente(**row) for row in rows]

    @staticmethod
    def cerca_utenti(query: str) -> list[Utente]:
        with db_connection.connect() as con:
            rows = con.execute(
                "SELECT * FROM utenti WHERE telegram_username LIKE ?", (f"%{query}%",)
            ).fetchall()
            return [Utente(**row) for row in rows]

    @staticmethod
    def aggiorna_nome(telegram_user_id: int, nuovo_nome: str) -> None:
        with db_connection.connect() as con:
            con.execute(
                "UPDATE utenti SET telegram_username = ? WHERE telegram_user_id = ?",
                (nuovo_nome, telegram_user_id)
            )