require('dotenv').config();

module.exports = Object.freeze({
  JWT_EXPIRES_IN_1H: '1h',
  JWT_EXPIRES_IN_20M: '20m',
  TOKEN_LIFESPAN: 3600 * 1000,
  MAX_FILE_SIZE: 3 * 1024 * 1024,
  ROLE: {
    ADMIN: '1',
    MEMBER: '2'
  },
  URL_PROTOCOL_REGEX: /^(https?:\/\/)/,
  URL_DOMAIN_REGEX: /^https?:\/\/([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/,
});
