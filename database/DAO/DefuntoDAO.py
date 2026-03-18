from datetime import date
from database.Connessione import db_connection
from database.Entity.Defunto import Defunto
from config import Stato

_CAMPI_TESTUALI = {"nome", "cognome", "data_decesso", "telefono_delegante", "nome_delegante", "note"}

class DefuntoDAO:
    def _row_to_defunto(self, row) -> Defunto:
        return Defunto(
            id=row["id"],
            nome=row["nome"],
            cognome=row["cognome"],
            data_decesso=date.fromisoformat(row["data_decesso"]),
            telefono_delegante=row["telefono_delegante"],
            nome_delegante=row["nome_delegante"],
            note=row["note"],
            creato_il=date.fromisoformat(row["creato_il"]),
            aggiunto_da=row["aggiunto_da"],
            stato_ringraziamento=row["stato_ringraziamento"],
            stato_preci=row["stato_preci"],
            stato_trigesimo=row["stato_trigesimo"],
        )

    def add_defunto(self, nome: str, cognome: str, data_decesso: date,
                    telefono_delegante: str, aggiunto_da: int,
                    nome_delegante: str | None = None, note: str | None = None) -> None:
        with db_connection.connect() as con:
            con.execute(
                """
                INSERT INTO defunti (nome, cognome, data_decesso, telefono_delegante,
                                     nome_delegante, note, aggiunto_da)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, cognome, data_decesso.isoformat(), telefono_delegante,
                 nome_delegante, note, aggiunto_da)
            )

    def get_defunto(self, defunto_id: int) -> Defunto | None:
        with db_connection.connect() as con:
            row = con.execute("SELECT * FROM defunti WHERE id = ?", (defunto_id,)).fetchone()
            return self._row_to_defunto(row) if row else None
        
    def get_tutti_defunti(self) -> list[Defunto]:
        with db_connection.connect() as con:
            rows = con.execute(
                "SELECT * FROM defunti ORDER BY data_decesso DESC"
            ).fetchall()
            return [self._row_to_defunto(row) for row in rows]

    def aggiorna_stato(self, defunto_id: int, campo: str, nuovo_stato: str) -> None:
        if campo not in ("stato_ringraziamento", "stato_preci", "stato_trigesimo"):
            raise ValueError(f"Campo non valido: {campo!r}")
        if nuovo_stato not in Stato.TUTTI:
            raise ValueError(f"Stato non valido: {nuovo_stato!r}")
        with db_connection.connect() as con:
            con.execute(f"UPDATE defunti SET {campo} = ? WHERE id = ?", (nuovo_stato, defunto_id))
    
    def aggiorna_campo(self, defunto_id: int, campo: str, valore) -> None:
        """Aggiorna un campo testuale (nome, cognome, data_decesso, telefono_delegante)."""
        if campo not in _CAMPI_TESTUALI:
            raise ValueError(f"Campo non valido: {campo!r}")
        with db_connection.connect() as con:
            con.execute(f"UPDATE defunti SET {campo} = ? WHERE id = ?", (valore, defunto_id))

    def elimina_defunto(self, defunto_id: int) -> None:
        with db_connection.connect() as con:
            con.execute("DELETE FROM defunti WHERE id = ?", (defunto_id,))
    
    def cerca_defunti(self, query: str) -> list[Defunto]:
        termini = query.strip().split()
        with db_connection.connect() as con:
            if len(termini) == 1:
                t = f"%{termini[0]}%"
                rows = con.execute(
                    "SELECT * FROM defunti WHERE nome LIKE ? OR cognome LIKE ? ORDER BY data_decesso DESC",
                    (t, t)
                ).fetchall()
            else:
                a, b = f"%{termini[0]}%", f"%{termini[1]}%"
                rows = con.execute(
                    """SELECT * FROM defunti WHERE
                    (nome LIKE ? AND cognome LIKE ?) OR
                    (nome LIKE ? AND cognome LIKE ?)
                    ORDER BY data_decesso DESC""",
                    (a, b, b, a)
                ).fetchall()
        return [self._row_to_defunto(row) for row in rows]