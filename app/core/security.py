from passlib.context import CryptContext

import hashlib

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from dotenv import dotenv_values
from app.schemas.auth import TokenData
import secrets

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
ALGORITHM = get_algorithm = CONFIG.get("ALGORITHM", 'HS256')
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
        "sub": subject, #user email
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }


    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(encoded_token:str)->TokenData | None:
    if not encoded_token:
        return None
    try:
        decoded = jwt.decode(encoded_token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    sub = decoded.get('sub')
    exp = decoded.get('exp')
    now_ts = int(datetime.now(timezone.utc).timestamp())

    if not isinstance(sub, str) or not sub:
        return None
    if not isinstance(exp, int) or exp <= now_ts:
        return None
    
    return TokenData(sub=sub, exp=exp)

def generate_refresh_token() -> str:
   return secrets.token_urlsafe(32)

def hash_refresh_token(token:str) -> str:
    pepper = (CONFIG.get("SECRET_KEY") or "").encode("utf-8")
    token_bytes = token.encode("utf-8") 
    return hashlib.sha256(token_bytes + pepper).hexdigest()

def verify_refresh_token(token:str, hashed_token:str)->bool:
    return secrets.compare_digest(hash_refresh_token(token), hashed_token)
