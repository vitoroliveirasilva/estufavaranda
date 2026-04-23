from __future__ import annotations

from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


def _rate_limit_key() -> str:
    return get_remote_address() or "unknown"


db = SQLAlchemy(session_options={"expire_on_commit": False})
migrate = Migrate(compare_type=True)
cors = CORS()
limiter = Limiter(key_func=_rate_limit_key, default_limits=[])
