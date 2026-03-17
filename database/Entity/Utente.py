from dataclasses import dataclass

@dataclass
class Utente:
    id:                 int
    telegram_user_id:   int
    username:           str | None
    is_admin:           bool
    is_active:          bool