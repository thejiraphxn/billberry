from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.user.auth import router as auth_router
from api.business.category import router as business_category_router
from api.business.business import router as business_router
from api.business.receipt import router as receipt_router
from api.business.product.product import router as product_router
from database import get_conn


app = FastAPI(
    title="BillBerry API",
    description="BillBerry: Secure Face-Classified Image Storage API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(business_router)
app.include_router(receipt_router)
app.include_router(business_category_router)
app.include_router(product_router)

@app.get("/")
def root():
    return {"message": "BillBerry API is running!"}

@app.get("/test-db")
def test_db():
    try:
        conn = get_conn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchone()
        conn.close()
        return {"status": "success", "message": "Database connection successful", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5002, reload=True)