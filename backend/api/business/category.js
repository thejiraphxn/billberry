const express = require('express');
const router = express.Router();
const { pool } = require('../../database/database');

router.get('/getAll', async (req, res) => {
  try {
    const [categories] = await pool.query(
      'SELECT category_id, category_name FROM business_categories'
    );
    res.json({
      success: true,
      categories
    });
  } catch (e) {
    res.status(500).json({
      success: false,
      detail: `เกิดข้อผิดพลาด: ${e.message}`
    });
  }
});

module.exports = router;
