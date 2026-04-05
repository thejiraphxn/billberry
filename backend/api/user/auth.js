const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');
const jwt = require('jsonwebtoken');
const { pool } = require('../../database/database');
const { createAccessToken } = require('../../function/jwt/jwt');


router.post('/signup', async (req, res) => {
  const {
    usr_username, usr_password, usr_firstname, usr_lastname,
    usr_email, confirm_password, usr_phone
  } = req.body;

  if (usr_password !== confirm_password) {
    return res.status(400).json({ status: false, message: "Passwords do not match." });
  }

  try {
    const [rows] = await pool.query(
      "SELECT 1 FROM users WHERE usr_username = ? OR usr_email = ? LIMIT 1",
      [usr_username, usr_email]
    );
    if (rows.length > 0) {
      return res.status(409).json({ status: false, message: "Username or email already exists." });
    }

    const hashed_pw = await bcrypt.hash(usr_password, 10);
    const user_gen_id = uuidv4();
    const now_th = new Date().toLocaleString("sv-SE", { timeZone: "Asia/Bangkok" }).replace('T', ' ').slice(0, 19);

    await pool.query(
      `INSERT INTO users
      (usr_id, usr_username, usr_email, usr_password_hash, usr_firstname, usr_lastname, usr_phone, usr_role, usr_created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        user_gen_id, usr_username, usr_email, hashed_pw,
        usr_firstname, usr_lastname, usr_phone || null,
        'general', now_th
      ]
    );

    res.json({ status: true, message: "Sign up successful!" });
  } catch (err) {
    res.status(500).json({ status: false, message: err.message });
  }
});

router.post('/signin', async (req, res) => {
  const { usr_username, usr_password } = req.body;

  try {
    const [rows] = await pool.query(
      "SELECT * FROM users WHERE usr_username = ? LIMIT 1",
      [usr_username]
    );
    const user = rows[0];
    if (!user) {
      return res.status(404).json({ status: false, message: "User not found." });
    }
    const pwOk = await bcrypt.compare(usr_password, user.usr_password_hash);
    if (!pwOk) {
      return res.status(401).json({ status: false, message: "Invalid password." });
    }

    const payload = {
      usr_id: user.usr_id,
      usr_username: user.usr_username,
      usr_email: user.usr_email,
      usr_firstname: user.usr_firstname,
      usr_lastname: user.usr_lastname,
      usr_avatar_url: user.usr_avatar_url,
      usr_role: user.usr_role,
      usr_phone: user.usr_phone,
    };
    const token = createAccessToken(payload);

    res.json({
      status: true,
      message: "Login successful.",
      token,
      user: payload
    });
  } catch (err) {
    res.status(500).json({ status: false, message: err.message });
  }
});

module.exports = router;
