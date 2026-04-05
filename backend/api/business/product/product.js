const express = require('express');
const router = express.Router();
const { pool } = require('../../../database/database');
const { decodeAccessToken } = require('../../../function/jwt/jwt');
const { v4: uuidv4 } = require('uuid');

// --------- Create Product ----------
router.post('/create', async (req, res) => {
  const authorization = req.headers['authorization'];
  if (!authorization || !authorization.startsWith('Bearer ')) {
    return res.status(401).json({ detail: 'Invalid token format' });
  }

  let payload;
  try {
    payload = decodeAccessToken(authorization.split(' ')[1]);
  } catch (err) {
    return res.status(401).json({ detail: 'Token invalid' });
  }

  const usr_id = payload.usr_id;
  const data = req.body;

  // --- Validation (required) ---
  if (!usr_id) return res.status(401).json({ detail: 'Invalid user' });
  if (!data.biz_id || !data.bp_pname || !data.pc_id || !data.pu_id) {
    return res.status(400).json({ detail: 'Missing required fields' });
  }

  // --- Validate/convert numeric fields ---
  try {
    if (data.bp_price !== undefined && data.bp_price !== null) data.bp_price = parseFloat(data.bp_price);
    if (data.bp_cost !== undefined && data.bp_cost !== null) data.bp_cost = parseFloat(data.bp_cost);
    if (data.bp_nowstock !== undefined && data.bp_nowstock !== null) data.bp_nowstock = parseFloat(data.bp_nowstock);
    if (data.bp_stock_enable !== undefined && data.bp_stock_enable !== null) {
      data.bp_stock_enable = parseInt(data.bp_stock_enable, 10);
      if (![0, 1].includes(data.bp_stock_enable)) throw new Error();
    } else {
      data.bp_stock_enable = 0;
    }
  } catch {
    return res.status(400).json({ detail: 'Invalid data type for number fields' });
  }

  // --- Duplicate check: barcode/SKU ใน biz เดียวกันเท่านั้น ---
  try {
    if (data.bp_barid) {
      const [dupBar] = await pool.query(
        "SELECT bp_id FROM business_products WHERE biz_id = ? AND bp_barid = ?",
        [data.biz_id, data.bp_barid]
      );
      if (dupBar.length > 0) {
        return res.status(400).json({ detail: "Barcode นี้ถูกใช้ไปแล้วในระบบ" });
      }
    }
    if (data.bp_sku) {
      const [dupSku] = await pool.query(
        "SELECT bp_id FROM business_products WHERE biz_id = ? AND bp_sku = ?",
        [data.biz_id, data.bp_sku]
      );
      if (dupSku.length > 0) {
        return res.status(400).json({ detail: "SKU นี้ถูกใช้ไปแล้วในระบบ" });
      }
    }
  } catch (e) {
    return res.status(500).json({ detail: `Database check failed: ${e.message}` });
  }

  // --- Prepare for insert ---
  const bp_id = uuidv4();
  const now = new Date();
  const bp_added_ts = now.toLocaleString("sv-SE", { timeZone: "Asia/Bangkok" }).replace('T', ' ').slice(0, 19);
  const bp_last_update = bp_added_ts;

  try {
    await pool.query(
      `INSERT INTO business_products (
        bp_id, biz_id, bp_barid, bp_sku, bp_pname, bp_price, bp_cost, pc_id,
        pu_id, bp_nowstock, bp_stock_enable, bp_descr, bp_added_ts, bp_last_update
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        bp_id, data.biz_id, data.bp_barid || null, data.bp_sku || null, data.bp_pname,
        data.bp_price || null, data.bp_cost || null, data.pc_id, data.pu_id,
        data.bp_nowstock || null, data.bp_stock_enable, data.bp_descr || null,
        bp_added_ts, bp_last_update
      ]
    );
    return res.json({
      success: true,
      bp_id,
      added_at: bp_added_ts
    });
  } catch (e) {
    return res.status(500).json({ detail: "Insert failed" });
  }
});

// --------- Get Product Categories ----------
router.get('/category/getall/:bizid', async (req, res) => {
  const bizid = req.params.bizid;
  if (!bizid) {
    return res.json({ success: false, data: [], message: "Missing biz_id" });
  }
  try {
    const [rows] = await pool.query(
      "SELECT pc_id, pc_name FROM product_categories WHERE biz_id = ?",
      [bizid]
    );
    return res.json({ success: true, data: rows });
  } catch (e) {
    return res.json({ success: false, data: [], message: `Database error: ${e.message}` });
  }
});

// --------- Get Product Units ----------
router.get('/unit/getall/:bizid', async (req, res) => {
  const bizid = req.params.bizid;
  if (!bizid) {
    return res.json({ success: false, data: [], message: "Missing biz_id" });
  }
  try {
    const [rows] = await pool.query(
      "SELECT pu_id, pu_name FROM product_units WHERE biz_id = ?",
      [bizid]
    );
    return res.json({ success: true, data: rows });
  } catch (e) {
    return res.json({ success: false, data: [], message: `Database error: ${e.message}` });
  }
});

module.exports = router;
