require('dotenv').config();
const envSuffix = process.env.NODE_ENV ? `.${process.env.NODE_ENV}` : '';
const env = `.env${envSuffix}`;

const dotenv = require('dotenv');
const result = dotenv.config({ path: `./${env}` });

if (result.error) {
  console.error(`Failed to load environment file: ${env}`);
  process.exit(1);
}

const {
  MONGO_USER,
  MONGO_PASSWORD,
  MONGO_HOST,
  MONGO_PORT,
  MONGO_DBNAME,
  TEST_USER,
  TEST_PASSWORD,
  TEST_HOST,
  TEST_PORT,
  TEST_DBNAME,
  PROD_USER,
  PROD_PASSWORD,
  PROD_HOST,
  PROD_PORT,
  PROD_DBNAME,
} = process.env;

module.exports = {
  defaultTeamName: 'My Organisation',
  dev: {
    username: MONGO_USER,
    password: MONGO_PASSWORD,
    database: MONGO_DBNAME,
    host: MONGO_HOST,
    port: MONGO_PORT,
    dialect: 'mongodb', 
  },
  test: {
    username: TEST_USER,
    password: TEST_PASSWORD,
    database: TEST_DBNAME,
    host: TEST_HOST,
    port: TEST_PORT,
    dialect: 'mongodb',
  },
  prod: {
    username: PROD_USER,
    password: PROD_PASSWORD,
    database: PROD_DBNAME,
    host: PROD_HOST,
    port: PROD_PORT,
    dialect: 'mongodb',
  },
};
