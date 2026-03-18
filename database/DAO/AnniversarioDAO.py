from datetime import date
from database.Connessione import db_connection
from database.Entity.Anniversario import Anniversario
from config import Stato


class AnniversarioDAO:

    def _row_to_anniversario(self, row) -> Anniversario:
        return Anniversario(
            id=row["id"],
            defunto_id=row["defunto_id"],
            numero=row["numero"],
            data=date.fromisoformat(row["data"]),
            data_affissione=date.fromisoformat(row["data_affissione"]) if row["data_affissione"] else None,
            descrizione=row["descrizione"],
            stato=row["stato"],
        )

    def ricalcola_numeri(self, defunto_id: int) -> None:
        with db_connection.connect() as con:
            rows = con.execute(
                "SELECT id FROM anniversari WHERE defunto_id = ? ORDER BY data ASC",
                (defunto_id,)
            ).fetchall()
            for i, row in enumerate(rows, start=1):
                con.execute(
                    "UPDATE anniversari SET numero = ? WHERE id = ?",
                    (i, row["id"])
                )

    def add_anniversario(self, defunto_id: int, data: date,
                         data_affissione: date | None = None,
                         descrizione: str | None = None) -> None:
        with db_connection.connect() as con:
            con.execute(
                """INSERT INTO anniversari (defunto_id, data, data_affissione, descrizione)
                   VALUES (?, ?, ?, ?)""",
                (defunto_id, data.isoformat(),
                 data_affissione.isoformat() if data_affissione else None,
                 descrizione),
            )
        self.ricalcola_numeri(defunto_id)

    def get_by_defunto(self, defunto_id: int) -> list[Anniversario]:
        with db_connection.connect() as con:
            rows = con.execute(
                "SELECT * FROM anniversari WHERE defunto_id = ? ORDER BY numero DESC",
                (defunto_id,),
            ).fetchall()
        return [self._row_to_anniversario(r) for r in rows]

    def get_anniversario(self, anniversario_id: int) -> Anniversario | None:
        with db_connection.connect() as con:
            row = con.execute(
                "SELECT * FROM anniversari WHERE id = ?", (anniversario_id,)
            ).fetchone()
        return self._row_to_anniversario(row) if row else None

    def aggiorna_stato(self, anniversario_id: int, nuovo_stato: str) -> None:
        if nuovo_stato not in Stato.TUTTI:
            raise ValueError(f"Stato non valido: {nuovo_stato!r}")
        with db_connection.connect() as con:
            con.execute(
                "UPDATE anniversari SET stato = ? WHERE id = ?",
                (nuovo_stato, anniversario_id),
            )

    def aggiorna_campo(self, anniversario_id: int, campo: str, valore) -> None:
        if campo not in {"data", "data_affissione", "descrizione"}:
            raise ValueError(f"Campo non valido: {campo!r}")
        with db_connection.connect() as con:
            con.execute(
                f"UPDATE anniversari SET {campo} = ? WHERE id = ?",
                (valore, anniversario_id),
            )
        if campo == "data":
            a = self.get_anniversario(anniversario_id)
            self.ricalcola_numeri(a.defunto_id)

    def elimina_anniversario(self, anniversario_id: int) -> None:
        a = self.get_anniversario(anniversario_id)
        with db_connection.connect() as con:
            con.execute("DELETE FROM anniversari WHERE id = ?", (anniversario_id,))
        self.ricalcola_numeri(a.defunto_id)

    def get_tutti(self) -> list[Anniversario]:
        with db_connection.connect() as con:
            rows = con.execute("SELECT * FROM anniversari ORDER BY data").fetchall()
        return [self._row_to_anniversario(r) for r in rows]
    
    def conta_by_defunto(self, defunto_id: int) -> int:
        with db_connection.connect() as con:
            row = con.execute(
                "SELECT COUNT(*) FROM anniversari WHERE defunto_id = ?", (defunto_id,)
            ).fetchone()
        return row[0]

    def get_by_defunto_paginati(self, defunto_id: int, offset: int, limit: int = 5) -> list[Anniversario]:
        with db_connection.connect() as con:
            rows = con.execute(
                "SELECT * FROM anniversari WHERE defunto_id = ? ORDER BY numero DESC LIMIT ? OFFSET ?",
                (defunto_id, limit, offset)
            ).fetchall()
        return [self._row_to_anniversario(r) for r in rows]

    @staticmethod
    def label_numero(numero: int) -> str:
        return f"{numero}° anniversario"