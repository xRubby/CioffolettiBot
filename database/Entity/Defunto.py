from datetime import date
from dataclasses import dataclass, field
from config import Stato

@dataclass
class Defunto:
    id:                     int
    nome:                   str
    cognome:                str
    data_decesso:           date
    telefono_delegante:     str
    creato_il:              date
    aggiunto_da:            int
    nome_delegante:         str | None = None
    note:                   str | None = None
    stato_ringraziamento:   str = field(default=Stato.DA_FARE)
    stato_preci:            str = field(default=Stato.DA_FARE)
    stato_trigesimo:        str = field(default=Stato.DA_FARE)