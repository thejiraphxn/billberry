const express = require('express');
const router = express.Router();
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const { pool } = require('../../database/database');
const { decodeAccessToken } = require('../../function/jwt/jwt'); 
const UPLOAD_DIR = path.join(__dirname, '../../assets/uploads/business/logo');

// Ensure upload directory exists
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

// ========== Business Create ==========
router.post('/create', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }

  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Invalid or expired token" });
  }
  const usr_id = payload.usr_id;

  const biz = req.body;
  let errors = {};

  // Validation
  if (!biz.businessName || !biz.businessName.trim()) errors.businessName = "กรุณาระบุชื่อธุรกิจ";
  if (biz.businessType === "jur" && (!biz.businessTaxID || !biz.businessTaxID.trim())) errors.businessTaxID = "กรุณาระบุเลขประจำตัวผู้เสียภาษี";
  if (!["ind", "jur"].includes(biz.businessType)) errors.businessType = "กรุณาเลือกประเภทของธุรกิจ";
  if (!biz.businessCategory || !biz.businessCategory.trim()) errors.businessCategory = "กรุณาเลือกหมวดหมู่ของธุรกิจ";
  if (!biz.businessDescription || !biz.businessDescription.trim()) errors.businessDescription = "กรุณาระบุรายละเอียดธุรกิจ";

  if (Object.keys(errors).length > 0) {
    return res.status(400).json({ detail: errors });
  }

  // Handle Image
  const biz_id = uuidv4();
  const created_at = new Date().toLocaleString("sv-SE", { timeZone: "Asia/Bangkok" }).replace('T', ' ').slice(0, 19);
  let filename = null;
  let filepath = null;

  try {
    const [header, encoded] = biz.businessImage.split(',', 2);
    const extMatch = header.match(/image\/(png|jpeg|jpg|webp)/);
    const file_ext = extMatch ? extMatch[1].replace('jpeg', 'jpg') : 'png';
    filename = `${biz_id}.${file_ext}`;
    filepath = path.join(UPLOAD_DIR, filename);
    fs.writeFileSync(filepath, Buffer.from(encoded, 'base64'));
  } catch (err) {
    return res.status(400).json({ detail: "ไม่สามารถบันทึกภาพได้: " + err.message });
  }

  try {
    // Validate businessCategory exists
    const [catRows] = await pool.query(
      "SELECT 1 FROM business_categories WHERE category_id = ? LIMIT 1",
      [biz.businessCategory]
    );
    if (catRows.length === 0) {
      return res.status(404).json({ detail: { businessCategory: "หมวดหมู่ธุรกิจไม่ถูกต้อง" } });
    }

    // Insert business
    await pool.query(
      `INSERT INTO businesses (
          biz_id, usr_id, category_id, biz_name,
          biz_tax_id, biz_type, biz_description,
          biz_address, biz_logo_path, biz_created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        biz_id, usr_id, biz.businessCategory, biz.businessName,
        biz.businessTaxID || null, biz.businessType, biz.businessDescription,
        biz.businessAddress, filepath, created_at
      ]
    );
    return res.json({ success: true, message: "สร้างธุรกิจสำเร็จ", biz_id });
  } catch (err) {
    return res.status(500).json({ detail: "เกิดข้อผิดพลาด: " + err.message });
  }
});

// ========== Get Businesses ==========
router.get('/getBusinesses', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }
  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Invalid or expired token" });
  }
  const usr_id = payload.usr_id;

  try {
    const [businesses] = await pool.query(
      `SELECT 
          b.biz_id, b.biz_name, b.biz_tax_id, b.biz_type, b.biz_description,
          b.biz_address, b.biz_logo_path, b.biz_created_at,
          c.category_id, c.category_name
        FROM businesses b
        JOIN business_categories c ON b.category_id = c.category_id
        WHERE b.usr_id = ?
        ORDER BY b.biz_created_at DESC
        LIMIT 1`,
      [usr_id]
    );

    const result = businesses.map(biz => {
      let biz_logo_base64 = null;
      const logo_path = biz.biz_logo_path;
      if (logo_path && fs.existsSync(logo_path)) {
        const ext = path.extname(logo_path).toLowerCase();
        if ([".png", ".jpg", ".jpeg", ".webp"].includes(ext)) {
          try {
            const file = fs.readFileSync(logo_path);
            const mime_type = ext === ".png" ? "image/png" : "image/jpeg";
            biz_logo_base64 = `data:${mime_type};base64,${file.toString('base64')}`;
          } catch (err) {
            biz_logo_base64 = null;
          }
        }
      }
      const out = { ...biz, biz_logo_base64 };
      delete out.biz_logo_path;
      return out;
    });

    return res.json({ success: true, businesses: result });
  } catch (err) {
    return res.status(500).json({ detail: "เกิดข้อผิดพลาด: " + err.message });
  }
});

// ========== Check Business ========== 
router.get('/check/:biz_id', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }
  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Invalid or expired token" });
  }
  const usr_id = payload.usr_id;
  const { biz_id } = req.params;

  try {
    const [rows] = await pool.query(
      "SELECT 1 FROM businesses WHERE biz_id = ? AND usr_id = ? LIMIT 1",
      [biz_id, usr_id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ detail: "ไม่พบข้อมูลธุรกิจหรือคุณไม่มีสิทธิ์เข้าถึง" });
    }
    return res.json({ success: true, message: "ธุรกิจนี้สามารถเข้าถึงได้", access: true });
  } catch (err) {
    return res.status(500).json({ detail: "เกิดข้อผิดพลาด: " + err.message });
  }
});

module.exports = router;
