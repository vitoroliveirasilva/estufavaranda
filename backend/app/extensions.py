from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(session_options={"expire_on_commit": False})
migrate = Migrate()
cors = CORS()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
