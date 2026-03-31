from fastapi import APIRouter, HTTPException
from database import get_conn

router = APIRouter(prefix="/api/business/category", tags=["Business Category"])

@router.get("/getAll")
def get_categories():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT category_id, category_name FROM business_categories")
                categories = cur.fetchall()

        return {
            "success": True,
            "categories": categories
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")
