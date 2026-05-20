from datetime import datetime, timezone
from jose import jwt, JWTError
from schemas.auth import TokenData
from .config import load_config

#create endpoint that uses the crypt context and save the password in the table
#each time a login takes place verify the password with the hash
CONFIG = load_config()


SECRET_KEY = get_secret = CONFIG.get("SECRET_KEY", 'None')
ALGORITHM = get_algorithm = CONFIG.get("ALGORITHM", 'HS256')

def decode_access_token(encoded_token:str)->TokenData | None:
    if not encoded_token:
        return None
    try:
        decoded = jwt.decode(encoded_token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    sub = decoded.get('sub')
    exp = decoded.get('exp')
    user_id = decoded.get('user_id')
    now_ts = int(datetime.now(timezone.utc).timestamp())

    if not isinstance(sub, str) or not sub:
        return None
    if not isinstance(exp, int) or exp <= now_ts:
        return None
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    
    return TokenData(sub=sub, exp=exp, user_id=user_id)
