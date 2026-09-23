from passlib.hash import bcrypt
from db import get_usuario


def verify_login(login: str, password: str):
    user = get_usuario(login)
    if not user:
        return None
    if not bcrypt.verify(password, user["password_hash"]):
        return None
    return {"login": user["login"], "rol": user["rol"]}
