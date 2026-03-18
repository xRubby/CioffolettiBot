from dataclasses import dataclass
from datetime import date

@dataclass
class Anniversario:
    id:               int
    defunto_id:       int
    numero:           int
    data:             date
    data_affissione:  date | None
    descrizione:      str | None
    stato:            str