from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
import pytz
import uuid
from jwt.jwt import create_access_token

from database import get_conn
from settings import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

router = APIRouter(prefix="/api/auth")

class UserCreate(BaseModel):
    usr_username: str
    usr_password: str
    usr_firstname: str
    usr_lastname: str
    usr_email: EmailStr
    confirm_password: str
    usr_phone: str = None

class UserLogin(BaseModel):
    usr_username: str
    usr_password: str

@router.post("/signup")
def signup(user: UserCreate):
    print(user)
    if user.usr_password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM users WHERE usr_username = %s OR usr_email = %s LIMIT 1",
                (user.usr_username, user.usr_email)
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Username or email already exists.")

            hashed_pw = bcrypt.hashpw(user.usr_password.encode(), bcrypt.gensalt()).decode()
            now_th = datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%Y-%m-%d %H:%M:%S")
            user_gen_id = str(uuid.uuid4())

            cur.execute(
                """INSERT INTO users
                (usr_id, usr_username, usr_email, usr_password_hash, usr_firstname, usr_lastname, usr_phone, usr_role, usr_created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    user_gen_id,
                    user.usr_username,
                    user.usr_email,
                    hashed_pw,
                    user.usr_firstname,
                    user.usr_lastname,
                    user.usr_phone,
                    'general',
                    now_th
                )
            )
            conn.commit()
    return {"status": True, "message": "Sign up successful!"}

@router.post("/signin")
def signin(user: UserLogin):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE usr_username = %s LIMIT 1",
                (user.usr_username,)
            )
            user_row = cur.fetchone()
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found.")
            if not bcrypt.checkpw(user.usr_password.encode(), user_row["usr_password_hash"].encode()):
                raise HTTPException(status_code=401, detail="Invalid password.")

            payload = {
                "usr_id": user_row["usr_id"],
                "usr_username": user_row["usr_username"],
                "usr_email": user_row["usr_email"],
                "usr_firstname": user_row["usr_firstname"],
                "usr_lastname": user_row["usr_lastname"],
                "usr_avatar_url": user_row["usr_avatar_url"],
                "usr_role": user_row["usr_role"],
                "usr_phone": user_row["usr_phone"],
            }
            token = create_access_token(payload)

            return {
                "status": True,
                "message": "Login successful.",
                "token": token,
                "user": payload
            }
