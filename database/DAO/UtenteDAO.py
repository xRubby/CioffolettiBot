from database.Entity.Utente import Utente
from database.Connessione import db_connection


class UtenteDAO:


    def aggiungi_utente(telegram_user_id: int, username: str | None, is_admin: bool = False, is_active: bool = True) -> None:
        with db_connection.connect() as con:
            con.execute("""INSERT INTO utenti (telegram_user_id, username, is_admin, is_active) VALUES (?, ?, ?, ?)""",
                (telegram_user_id, username, int(is_admin), int(is_active)))

    def rimuovi_utente(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("""UPDATE utenti SET is_active = 0 WHERE id = ?""", (utente_id,))
    
    def riattiva_utente(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("""UPDATE utenti SET is_active = 1 WHERE id = ?""",(utente_id,))
    
    def rendi_admin(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("UPDATE utenti SET is_admin = 1 WHERE id = ?", (utente_id,))

    def disattiva_admin(utente_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("UPDATE utenti SET is_admin = 0 WHERE id = ?", (utente_id,))

    def get_utenti() -> list[Utente]:
        with db_connection.connect() as con:
            rows = con.execute("SELECT * FROM utenti").fetchall()
        return [Utente(**row) for row in rows]

    def get_utente(utente_id: int) -> Utente | None:
        with db_connection.connect() as con:
            row = con.execute("SELECT * FROM utenti WHERE id = ?", (utente_id,)).fetchone()
        return Utente(**row) if row else None