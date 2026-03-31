from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, field_validator
from database import get_conn
from datetime import datetime
import pytz
import uuid
from jwt.jwt import decode_access_token
from typing import Optional

router = APIRouter(prefix="/api/business/product", tags=["Product"])

# Pydantic Model
class ProductCreateRequest(BaseModel):
    biz_id: str
    bp_barid: Optional[str] = None
    bp_sku: Optional[str] = None
    bp_pname: str
    bp_price: Optional[float] = None
    bp_cost: Optional[float] = None
    pc_id: str
    pu_id: str
    bp_nowstock: Optional[float] = None
    bp_stock_enable: Optional[int] = 0
    bp_descr: Optional[str] = None

    @field_validator("bp_stock_enable")
    @classmethod
    def validate_stock_enable(cls, v):
        if v is None:
            return 0
        if v not in [0, 1]:
            raise ValueError("bp_stock_enable must be 0 or 1")
        return v


@router.post("/create")
def create_product(
    data: ProductCreateRequest,
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
    if not usr_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    if not data.biz_id or not data.bp_pname or not data.pc_id or not data.pu_id:
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        if data.bp_price is not None:
            data.bp_price = float(data.bp_price)
        if data.bp_cost is not None:
            data.bp_cost = float(data.bp_cost)
        if data.bp_nowstock is not None:
            data.bp_nowstock = float(data.bp_nowstock)
        if data.bp_stock_enable is not None:
            data.bp_stock_enable = int(data.bp_stock_enable)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid data type for number fields")

    # --- Check for duplicate barcode or sku ---
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Check barcode ซ้ำ
                if data.bp_barid:
                    cur.execute(
                        "SELECT bp_id FROM business_products WHERE biz_id = %s AND bp_barid = %s",
                        (data.biz_id, data.bp_barid)
                    )
                    if cur.fetchone():
                        raise HTTPException(status_code=400, detail="Barcode นี้ถูกใช้ไปแล้วในระบบ")
                # Check SKU ซ้ำ
                if data.bp_sku:
                    cur.execute(
                        "SELECT bp_id FROM business_products WHERE biz_id = %s AND bp_sku = %s",
                        (data.biz_id, data.bp_sku)
                    )
                    if cur.fetchone():
                        raise HTTPException(status_code=400, detail="SKU นี้ถูกใช้ไปแล้วในระบบ")
    except HTTPException as e:
        # re-raise ให้ FastAPI จัดการ
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database check failed: {e}")

    # --- Prepare to insert ---
    bp_id = str(uuid.uuid4())
    tz = pytz.timezone("Asia/Bangkok")
    now = datetime.now(tz)
    bp_added_ts = now.strftime("%Y-%m-%d %H:%M:%S")
    bp_last_update = bp_added_ts

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                sql = """
                INSERT INTO business_products (
                    bp_id, biz_id, bp_barid, bp_sku, bp_pname, bp_price, bp_cost, pc_id,
                    pu_id, bp_nowstock, bp_stock_enable, bp_descr, bp_added_ts, bp_last_update
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql, (
                    bp_id, data.biz_id, data.bp_barid, data.bp_sku, data.bp_pname, data.bp_price,
                    data.bp_cost, data.pc_id, data.pu_id, data.bp_nowstock,
                    data.bp_stock_enable, data.bp_descr, bp_added_ts, bp_last_update
                ))
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Insert failed")

    return {
        "success": True,
        "bp_id": bp_id,
        "added_at": bp_added_ts
    }



@router.get("/category/getall/{bizid}")
def get_categories(bizid: str):
    if not bizid:
        return {"success": False, "data": [], "message": "Missing biz_id"}
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pc_id, pc_name FROM product_categories WHERE biz_id = %s", (bizid,))
                rows = cur.fetchall()
        return {"success": True, "data": rows}
    except Exception as e:
        return {"success": False, "data": [], "message": f"Database error: {e}"}


@router.get("/unit/getall/{bizid}")
def get_units(bizid: str):
    if not bizid:
        return {"success": False, "data": [], "message": "Missing biz_id"}
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pu_id, pu_name FROM product_units WHERE biz_id = %s", (bizid,))
                rows = cur.fetchall()
        return {"success": True, "data": rows}
    except Exception as e:
        return {"success": False, "data": [], "message": f"Database error: {e}"}
