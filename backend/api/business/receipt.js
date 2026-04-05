const express = require('express');
const router = express.Router();
const { pool } = require('../../database/database');
const { decodeAccessToken } = require('../../function/jwt/jwt');
const { v4: uuidv4 } = require('uuid');
const moment = require('moment-timezone');

// ========== 1. CREATE RECEIPT ==========
router.post('/create', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }
  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Token invalid" });
  }
  const usr_id = payload.usr_id;
  const { business_id } = req.body;

  try {
    // 1. Check business
    const [bizRows] = await pool.query(
      "SELECT * FROM businesses WHERE biz_id = ? AND usr_id = ? LIMIT 1",
      [business_id, usr_id]
    );
    const business = bizRows[0];
    if (!business) {
      return res.status(400).json({ msg: "Invalid business data" });
    }
    const receipt_id = uuidv4();
    const created_at = moment().tz('Asia/Bangkok').format('YYYY-MM-DD HH:mm:ss');
    const running_number = moment().tz('Asia/Bangkok').format('YYYYMMDDHHmmss');

    // 2. Insert receipt
    const [result] = await pool.query(
      `INSERT INTO business_receipts (
        br_id, biz_id, br_runno, br_cname,
        br_created_ts, br_status, br_last_ts
      ) VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [
        receipt_id,
        business_id,
        running_number,
        "ลูกค้าทั่วไป",
        created_at,
        "DRAFT",
        created_at
      ]
    );

    if (result.affectedRows !== 1) {
      return res.status(500).json({ detail: "Receipt insert failed" });
    }
    return res.json({ success: true, receipt_id });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ detail: "Something went wrong" });
  }
});

// ========== 2. GET RECEIPTS ==========
router.get('/get_receipts/:business_id', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }
  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Token invalid" });
  }
  const usr_id = payload.usr_id;
  const { business_id } = req.params;

  try {
    // 1. check business owner
    const [bizRows] = await pool.query(
      "SELECT * FROM businesses WHERE biz_id = ? AND usr_id = ? LIMIT 1",
      [business_id, usr_id]
    );
    if (!bizRows.length) {
      return res.status(404).json({ detail: "Business not found or not allowed" });
    }
    // 2. get receipts
    const [receipts] = await pool.query(
      "SELECT * FROM business_receipts WHERE biz_id = ? ORDER BY br_created_ts DESC LIMIT 100",
      [business_id]
    );
    return res.json({ success: true, receipts });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ detail: "Something went wrong" });
  }
});

// ========== 3. CHECK EXIST RECEIPT ==========
router.get('/check_exist/:business_id/:br_id', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }
  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Token invalid" });
  }
  const usr_id = payload.usr_id;
  const { business_id, br_id } = req.params;

  try {
    // 1. check business owner
    const [bizRows] = await pool.query(
      "SELECT 1 FROM businesses WHERE biz_id = ? AND usr_id = ? LIMIT 1",
      [business_id, usr_id]
    );
    if (!bizRows.length) {
      return res.json({ success: false, receipt_id: null });
    }
    // 2. check receipt
    const [rows] = await pool.query(
      "SELECT br_id FROM business_receipts WHERE biz_id = ? AND br_id = ? LIMIT 1",
      [business_id, br_id]
    );
    if (rows.length) {
      return res.json({ success: true, receipt_id: rows[0].br_id });
    }
    return res.json({ success: false, receipt_id: null });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ detail: "Something went wrong" });
  }
});

// ========== 4. GET RECEIPT HEADER ==========
router.get('/get_receipt_header/:business_id/:br_id', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }
  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Token invalid" });
  }
  const usr_id = payload.usr_id;
  const { business_id, br_id } = req.params;

  try {
    const [rows] = await pool.query(
      "SELECT * FROM business_receipts WHERE biz_id = ? AND br_id = ? LIMIT 1",
      [business_id, br_id]
    );
    const receipt_header = rows[0];
    if (!receipt_header) {
      return res.status(404).json({ detail: "Receipt not found" });
    }
    // ตรวจสอบ member/contact
    let member = { is_member: false, member_data: null };
    const bct_id = receipt_header.bct_id;
    if (bct_id && String(bct_id).trim() !== "") {
      const [contactRows] = await pool.query(
        "SELECT * FROM business_contacts WHERE biz_id = ? AND bct_id = ? LIMIT 1",
        [business_id, bct_id]
      );
      if (contactRows.length) {
        member = { is_member: true, member_data: contactRows[0] };
      }
    }
    return res.json({
      success: true,
      receipt_header: { header_data: receipt_header, member }
    });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ detail: "Something went wrong" });
  }
});

// ========== 5. UPDATE RECEIPT HEADER ==========
router.put('/update_header', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid token format" });
  }
  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (e) {
    return res.status(401).json({ detail: "Token invalid" });
  }
  const usr_id = payload.usr_id;
  const data = req.body;

  // Validate required fields
  if (!data.br_id || !data.biz_id || !data.br_id.trim() || !data.biz_id.trim()) {
    return res.status(400).json({ detail: "ต้องระบุข้อมูล br_id และ biz_id" });
  }
  if (data.br_phone && !/^\d+$/.test(data.br_phone)) {
    return res.status(400).json({ detail: "เบอร์โทรต้องเป็นตัวเลขเท่านั้น" });
  }

  try {
    // Check old receipt
    const [oldRows] = await pool.query(
      "SELECT bct_id, br_runno FROM business_receipts WHERE br_id = ? AND biz_id = ?",
      [data.br_id, data.biz_id]
    );
    const old_row = oldRows[0];
    if (!old_row) {
      return res.status(404).json({ detail: "ไม่พบใบเสร็จนี้" });
    }
    // Prepare update
    const br_last_ts = moment().tz('Asia/Bangkok').format('YYYY-MM-DD HH:mm:ss');
    const update_data = {
      ...data,
      bct_id: old_row.bct_id,
      br_runno: old_row.br_runno,
      br_last_ts,
      br_cname: data.br_cname || "",
      br_caddess: data.br_caddess || "",
      br_phone: data.br_phone || "",
      br_taxid: data.br_taxid || ""
    };
    // Update
    await pool.query(
      `UPDATE business_receipts SET
        br_cname = ?, br_caddess = ?, br_phone = ?, br_taxid = ?, br_last_ts = ?
      WHERE br_id = ? AND biz_id = ?`,
      [
        update_data.br_cname,
        update_data.br_caddess,
        update_data.br_phone,
        update_data.br_taxid,
        update_data.br_last_ts,
        update_data.br_id,
        update_data.biz_id
      ]
    );
    return res.json({
      success: true,
      message: "อัปเดตข้อมูลเรียบร้อย",
      header_data: update_data,
      updated_by: usr_id
    });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ detail: "Something went wrong" });
  }
});

module.exports = router;
