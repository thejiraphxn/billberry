from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from database import get_conn
from datetime import datetime
import pytz
import uuid
import os
from jwt.jwt import decode_access_token
import base64


router = APIRouter(prefix="/api/business", tags=["Business"])

UPLOAD_DIR = "assets/uploads/business/logo"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class BusinessCreate(BaseModel):
    businessName: str
    businessTaxID: str = None
    businessType: str
    businessCategory: str
    businessAddress: str
    businessDescription: str
    businessImage: str

@router.post("/create")
def createBusiness(biz: BusinessCreate, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    usr_id = payload.get("usr_id")
    
    print(biz)
    
    errors = {}

    if not biz.businessName.strip():
        errors["businessName"] = "กรุณาระบุชื่อธุรกิจ"

    if biz.businessType == "jur" and (not biz.businessTaxID or not biz.businessTaxID.strip()):
        errors["businessTaxID"] = "กรุณาระบุเลขประจำตัวผู้เสียภาษี"

    if biz.businessType not in ["ind", "jur"]:
        errors["businessType"] = "กรุณาเลือกประเภทของธุรกิจ"

    if not biz.businessCategory or biz.businessCategory == "":
        errors["businessCategory"] = "กรุณาเลือกหมวดหมู่ของธุรกิจ"

    if not biz.businessDescription.strip():
        errors["businessDescription"] = "กรุณาระบุรายละเอียดธุรกิจ"

    if errors:
        raise HTTPException(status_code=400, detail=errors)

    biz_id = str(uuid.uuid4())
    created_at = datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M:%S")

    try:
        header, encoded = biz.businessImage.split(",", 1)
        file_ext = header.split("/")[1].split(";")[0]  # เช่น png, jpeg
        filename = f"{biz_id}.{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(encoded))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ไม่สามารถบันทึกภาพได้: {str(e)}")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM business_categories WHERE category_id = %s LIMIT 1",
                    (biz.businessCategory,)
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail={"businessCategory": "หมวดหมู่ธุรกิจไม่ถูกต้อง"})

                cur.execute("""
                    INSERT INTO businesses (
                        biz_id, usr_id, category_id, biz_name,
                        biz_tax_id, biz_type, biz_description,
                        biz_address, biz_logo_path, biz_created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    biz_id,
                    usr_id,
                    biz.businessCategory,
                    biz.businessName,
                    biz.businessTaxID if biz.businessTaxID else None,
                    biz.businessType,
                    biz.businessDescription,
                    biz.businessAddress,
                    filepath,
                    created_at
                ))
                conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

    return {"success": True, "message": "สร้างธุรกิจสำเร็จ", "biz_id": biz_id}


@router.get("/getBusinesses")
def get_businesses(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    usr_id = payload.get("usr_id")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        b.biz_id,
                        b.biz_name,
                        b.biz_tax_id,
                        b.biz_type,
                        b.biz_description,
                        b.biz_address,
                        b.biz_logo_path,
                        b.biz_created_at,
                        c.category_id,
                        c.category_name
                    FROM businesses b
                    JOIN business_categories c ON b.category_id = c.category_id
                    WHERE b.usr_id = %s
                    ORDER BY b.biz_created_at DESC
                    LIMIT 1
                """, (usr_id,))
                businesses = cur.fetchall()

        result = []
        for biz in businesses:
            logo_path = biz.get("biz_logo_path")
            biz["biz_logo_base64"] = None

            if logo_path and os.path.exists(logo_path):
                ext = os.path.splitext(logo_path)[1].lower()
                if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                    try:
                        with open(logo_path, "rb") as img_file:
                            encoded = base64.b64encode(img_file.read()).decode('utf-8')
                            mime_type = "image/png" if ext == ".png" else "image/jpeg"
                            biz["biz_logo_base64"] = f"data:{mime_type};base64,{encoded}"
                    except Exception as e:
                        print(f"Failed to encode image {logo_path}: {e}")
                        biz["biz_logo_base64"] = None
            else:
                biz["biz_logo_base64"] = None

            del biz["biz_logo_path"]
            result.append(biz)

        return {
            "success": True,
            "businesses": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")

@router.get("/check/{biz_id}")
def check_exists(biz_id: str, authorization: str = Header(...)):
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    usr_id = payload.get("usr_id")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM businesses WHERE biz_id = %s AND usr_id = %s LIMIT 1",
                    (biz_id, usr_id)
                )
                exists = cur.fetchone()
                if not exists:
                    raise HTTPException(status_code=404, detail="ไม่พบข้อมูลธุรกิจหรือคุณไม่มีสิทธิ์เข้าถึง")

        return { "success": True, "message": "ธุรกิจนี้สามารถเข้าถึงได้", "access": True }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")