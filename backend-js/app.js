const express = require('express');
const cors = require('cors');
const PORT = 5002;
const authRouter = require('./api/user/auth');
const businessRouter = require('./api/business/business');
const businessCategoryRouter = require('./api/business/category');
const receiptRouter = require('./api/business/receipt');
const productRouter = require('./api/business/product/product');

const { pool } = require('./database/database');

const app = express();

app.use(express.json());
app.use(cors({
  origin: "*", 
  credentials: true,
}));


app.use('/api/auth', authRouter);
app.use('/api/business', businessRouter);
app.use('/api/business/category', businessCategoryRouter);
app.use('/api/business/receipt', receiptRouter);
app.use('/api/business/product', productRouter);

app.get('/', (req, res) => {
  res.json({ message: "BillBerry API is running!" });
});


app.get('/test-db', async (req, res) => {
    let conn;
    try {
      conn = await pool.getConnection();
      const [rows] = await conn.query('SELECT * FROM users LIMIT 1');
      conn.release();  // คืน connection ให้ pool
      res.json({ status: "success", message: "Database connection successful", result: rows[0] });
    } catch (e) {
      if (conn) conn.release();
      res.json({ status: "error", message: e.message });
    }
});
  

app.listen(PORT, () => {
  console.log(`Server running at http://127.0.0.1:${PORT}`);
});
