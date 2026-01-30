from app.db.base import Base
from app.db.session import engine
from app.models.auth_session import AuthSession

from app.models.user import User

def init_db()->None:
    Base.metadata.create_all(bind=engine)