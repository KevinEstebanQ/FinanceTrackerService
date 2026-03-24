from db.base import Base
from db.session import engine
from models.auth_session import AuthSession
from models.user import User

def init_db()->None:
    print("Creating tables")
    Base.metadata.create_all(bind=engine)
    print("Tables created")