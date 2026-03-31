from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, field_validator
from database import get_conn
from datetime import datetime
import pytz
import uuid
import os
from jwt.jwt import decode_access_token
import base64
from typing import Optional


router = APIRouter(prefix="/api/business/receipt", tags=["Receipt"])

class ReceiptCreate(BaseModel):
    business_id: str

@router.post("/create")
def createBusiness(rc: ReceiptCreate, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid")
    
    usr_id = payload.get("usr_id")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # 1. เช็ค business
                cur.execute(
                    "SELECT * FROM businesses WHERE biz_id = %s AND usr_id = %s LIMIT 1",
                    (rc.business_id, usr_id,)
                )
                business = cur.fetchone()
                if business is None:
                    raise HTTPException(status_code=400, detail={"msg": "Invalid business data"})

                business_id = business.get("biz_id")
                receipt_id = str(uuid.uuid4())
                created_at = datetime.now(pytz.timezone("Asia/Bangkok"))
                running_number = created_at.strftime("%Y%m%d%H%M%S")

                # 2. Insert receipt
                cur.execute("""
                    INSERT INTO business_receipts (
                        br_id, biz_id, br_runno, br_cname,
                        br_created_ts, br_status, br_last_ts
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    receipt_id,
                    business_id,
                    running_number,
                    "ลูกค้าทั่วไป",
                    created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "DRAFT", 
                    created_at.strftime("%Y-%m-%d %H:%M:%S")
                ))

                # 3. เช็ค rowcount หลัง insert
                if cur.rowcount != 1:
                    raise HTTPException(status_code=500, detail="Receipt insert failed")

                conn.commit()

                return {
                    "success": True,
                    "receipt_id": receipt_id,
                }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/get_receipts/{business_id}")
def getReceipts(business_id: str, authorization: str = Header(...)):
    # 1. ตรวจสอบ Bearer Token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid")
    
    usr_id = payload.get("usr_id")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # 2. เช็คว่า user เป็นเจ้าของ business นี้
                cur.execute(
                    "SELECT * FROM businesses WHERE biz_id = %s AND usr_id = %s LIMIT 1",
                    (business_id, usr_id)
                )
                business = cur.fetchone()

                if business is None:
                    raise HTTPException(status_code=404, detail="Business not found or not allowed")

                # 3. ดึง receipts ทั้งหมดของ business นี้
                cur.execute(
                    "SELECT * FROM business_receipts WHERE biz_id = %s ORDER BY br_created_ts DESC LIMIT 100",
                    (business_id,)
                )
                receipts = cur.fetchall()

                return {
                    "success": True,
                    "receipts": receipts 
                }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/check_exist/{business_id}/{br_id}")
def ReceiptExist(business_id: str, br_id: str, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid")

    usr_id = payload.get("usr_id")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                
                cur.execute(
                    "SELECT 1 FROM businesses WHERE biz_id = %s AND usr_id = %s LIMIT 1",
                    (business_id, usr_id)
                )
                if cur.fetchone() is None:
                    return {
                        "success": False,
                        "receipt_id": None
                    }
                
                cur.execute(
                    "SELECT br_id FROM business_receipts WHERE biz_id = %s AND br_id = %s LIMIT 1",
                    (business_id, br_id)
                )
                result = cur.fetchone()
                if result:
                    return {
                        "success": True,
                        "receipt_id": result['br_id']
                    }
                else:
                    return {
                        "success": False,
                        "receipt_id": None
                    }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/get_receipt_header/{business_id}/{br_id}")
def getReceiptHeader(business_id: str, br_id: str, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid")

    usr_id = payload.get("usr_id")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM business_receipts WHERE biz_id = %s AND br_id = %s LIMIT 1",
                    (business_id, br_id)
                )
                receipt_header = cur.fetchone()

                if not receipt_header:
                    raise HTTPException(status_code=404, detail="Receipt not found")
                
                # ตรวจสอบ member (contact)
                bct_id = receipt_header.get('bct_id', None)
                member = {"is_member": False, "member_data": None}

                if bct_id and str(bct_id).strip() != "":
                    cur.execute(
                        "SELECT * FROM business_contacts WHERE biz_id = %s AND bct_id = %s LIMIT 1",
                        (business_id, bct_id)
                    )
                    bus_contact = cur.fetchone()
                    if bus_contact:
                        member = {
                            "is_member": True,
                            "member_data": bus_contact
                        }

                return {
                    "success": True,
                    "receipt_header": {"header_data": receipt_header, "member": member}
                }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong")


class ReceiptUpdateHeader(BaseModel):
    br_id: str
    biz_id: str
    br_cname: Optional[str] = None
    br_caddess: Optional[str] = None
    br_phone: Optional[str] = None
    br_taxid: Optional[str] = None

    @field_validator("br_id", "biz_id")
    @classmethod
    def required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("ต้องระบุข้อมูล")
        return v


    @field_validator("br_phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return v


@router.put('/update_header')
async def update_receipt_header(
    data: ReceiptUpdateHeader,
    authorization: str = Header(...)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid")

    usr_id = payload.get("usr_id")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT bct_id, br_runno FROM business_receipts WHERE br_id=%s AND biz_id=%s",
                    (data.br_id, data.biz_id)
                )
                old_row = cur.fetchone()
                if not old_row:
                    raise HTTPException(status_code=404, detail="ไม่พบใบเสร็จนี้")

                # .dict() เพื่อให้เป็น dict จริง
                update_data = data.model_dump()
                update_data['bct_id'] = old_row['bct_id']
                update_data['br_runno'] = old_row['br_runno']

                # Set br_last_ts เป็น timestamp ปัจจุบัน
                update_data['br_last_ts'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # กัน None -> "" ถ้า schema ใน DB เป็น NOT NULL
                for k in ['br_cname', 'br_caddess', 'br_phone', 'br_taxid']:
                    if update_data[k] is None:
                        update_data[k] = ""

                sql = """
                    UPDATE business_receipts
                    SET
                        br_cname = %(br_cname)s,
                        br_caddess = %(br_caddess)s,
                        br_phone = %(br_phone)s,
                        br_taxid = %(br_taxid)s,
                        br_last_ts = %(br_last_ts)s
                    WHERE
                        br_id = %(br_id)s AND biz_id = %(biz_id)s
                """
                cur.execute(sql, update_data)
                conn.commit()

                return {
                    "success": True,
                    "message": "อัปเดตข้อมูลเรียบร้อย",
                    "header_data": update_data,
                    "updated_by": usr_id
                }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong")