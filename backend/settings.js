require('dotenv').config();

module.exports = {
  JWT_SECRET: process.env.JWT_SECRET,
  JWT_ALGORITHM: process.env.JWT_ALGORITHM || 'HS256',
  ACCESS_TOKEN_EXPIRE_HOURS: Number(process.env.ACCESS_TOKEN_EXPIRE_HOURS) || 12,
};
