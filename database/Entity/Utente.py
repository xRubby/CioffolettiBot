from dataclasses import dataclass

@dataclass
class Utente:
    id:                 int
    telegram_user_id:   int
    telegram_username:  str | None
    is_admin:           bool
    is_active:          bool