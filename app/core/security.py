from passlib.context import CryptContext

#create endpoint that uses the crypt context and save the password in the table
#each time a login takes place verify the password with the hash

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password: str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str)->bool:
    return pwd_context.verify(plain_password, hashed_password)