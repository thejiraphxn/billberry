const jwt = require('jsonwebtoken');
const { JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS } = require('../../settings');

function createAccessToken(data, expiresInHours = ACCESS_TOKEN_EXPIRE_HOURS) {
  return jwt.sign(
    { ...data },
    JWT_SECRET,
    { algorithm: JWT_ALGORITHM, expiresIn: `${expiresInHours}h` }
  );
}

function decodeAccessToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET, { algorithms: [JWT_ALGORITHM] });
  } catch (err) {
    if (err.name === 'TokenExpiredError') throw new Error('Token expired');
    throw new Error('Token invalid');
  }
}

module.exports = { createAccessToken, decodeAccessToken };
