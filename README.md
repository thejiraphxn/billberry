# BillBerry

BillBerry เป็นโปรเจกต์ที่ประกอบด้วย **Frontend (Next.js)** และ **Backend** (มีให้เลือก 2 แบบ: Node/Express หรือ Python/FastAPI) โดย API ทำงานบนพอร์ต `5002` และ Frontend ใช้ API ผ่านตัวแปรแวดล้อม

BillBerry is a project with a **Next.js frontend** and **two backend options** (Node/Express or Python/FastAPI). The API runs on port `5002`, and the frontend calls it via environment variables.

## Project structure / โครงสร้างโปรเจกต์

- `frontend/`: Next.js app (React 19)
- `backend-js/`: Express API (CommonJS)
- `backend-py/`: FastAPI API (Python)

## Prerequisites / สิ่งที่ต้องมี

- **Node.js + npm** (สำหรับ `frontend/` และ `backend-js/`)
- **Python 3.12+** (สำหรับ `backend-py/` หากเลือกใช้)
- **MySQL** (โปรเจกต์ตั้งค่าไว้เป็น `localhost:8889`, database: `BillBerry`)

> หมายเหตุ/Note: ตอนนี้ backend ทั้ง 2 แบบตั้งค่า DB แบบ hard-code (`root/root`, port `8889`) ในโค้ด ควรย้ายไปใช้ `.env` ในภายหลังเพื่อความปลอดภัย

## Environment variables / ตัวแปรแวดล้อม

### Frontend (`frontend/`)

ไฟล์ที่พบ: `frontend/.env.development`

Common variables:

- `NEXT_PUBLIC_API_URL`: URL ของ backend API เช่น `http://localhost:5002`
- `NEXTAUTH_SECRET`: secret สำหรับ NextAuth (**ไม่ควร commit ค่า secret**)

แนะนำให้ใช้ไฟล์เช่น `.env.local` สำหรับค่าที่เป็น secret ในเครื่องตัวเอง

### Backend JS (`backend-js/`)

ไฟล์ที่พบ: `backend-js/.env` (ใช้สำหรับ JWT settings)

### Backend PY (`backend-py/`)

พบค่า JWT ใน `backend-py/settings.py` (ตอนนี้เป็นค่าในโค้ด)

## Run the project / วิธีรันโปรเจกต์

### 1) Backend (เลือกอย่างใดอย่างหนึ่ง) / Choose ONE backend

#### Option A: Node/Express (`backend-js`)

```bash
cd backend-js
npm install
npm run start
```

API: `http://127.0.0.1:5002`

Useful endpoints:

- `GET /` -> health message
- `GET /test-db` -> test MySQL connection

#### Option B: Python/FastAPI (`backend-py`)

ถ้าใช้ virtualenv ที่มีอยู่แล้ว (`backend-py/env`) ให้ activate ก่อน จากนั้นค่อยรัน

```bash
cd backend-py
python main.py
```

API: `http://127.0.0.1:5002`

Useful endpoints:

- `GET /` -> health message
- `GET /test-db` -> test MySQL connection

> หมายเหตุ/Note: โปรเจกต์นี้มีโฟลเดอร์ `backend-py/env` (virtual environment) อยู่ใน workspace ซึ่งปกติ **ไม่ควร commit** และได้ถูกเพิ่มใน `.gitignore` ระดับ root แล้ว

### 2) Frontend (`frontend`)

```bash
cd frontend
npm install
npm run dev
```

Frontend: โดยปกติจะอยู่ที่ `http://localhost:3000`

## Development notes / หมายเหตุสำหรับการพัฒนา

- **Port collision**: backend ทั้ง 2 ตัวใช้ port `5002` เหมือนกัน ดังนั้นรันได้ทีละตัว
- **CORS**: backend เปิด `allow_origins=["*"]`/`origin: "*"` สำหรับ dev

# billberry
