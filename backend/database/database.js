const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: 'localhost',
  port: 8889,
  user: 'root',
  password: 'root',
  database: 'BillBerry',
  charset: 'utf8mb4',
  waitForConnections: true,
  connectionLimit: 10,   // ปรับตามต้องการ
  queueLimit: 0
});

module.exports = { pool };
