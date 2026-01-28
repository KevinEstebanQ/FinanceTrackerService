from passlib.context import CryptContext

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from dotenv import dotenv_values

#create endpoint that uses the crypt context and save the password in the table
#each time a login takes place verify the password with the hash
CONFIG = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env")
    }

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password: str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str)->bool:
    return pwd_context.verify(plain_password, hashed_password)

SECRET_KEY = get_secret = CONFIG.get("SECRET_KEY", 'None')
ALGORTIHM = get_algorithm = CONFIG.get("ALGORITHM", 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES  = int(CONFIG.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
                                   
def create_access_token(subject:str, expires_delta: timedelta  | None = None)->str:
    """
    create a signed jwt Containing subject and expiration time
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    expire = now  + expires_delta

    to_encode = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }


    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORTIHM)

    return encoded_jwt
