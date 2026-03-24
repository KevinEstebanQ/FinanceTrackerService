from db.base import Base
from db.session import engine
from models.transactions import Transaction

def init_db()->None:
    Base.metadata.create_all(bind=engine)