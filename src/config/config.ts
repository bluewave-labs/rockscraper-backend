import dotenv from 'dotenv';

// load environment from the correct .env file based on the NODE_ENV variable (dev, prod, test)
dotenv.config();
const suffix = `.${process.env.NODE_ENV ?? 'dev'}`;
dotenv.config({ path: `./.env${suffix}` });

console.log({ env: process.env.NODE_ENV });

const requiredEnvVars = [
  'MONGO_HOST',
  'MONGO_PORT',
  'MONGO_DBNAME',
  'MONGO_USER',
  'MONGO_PASSWORD',
  'REDIS_HOST',
  'REDIS_PORT',
  'REDIS_DB',
];
const missingEnvVars = requiredEnvVars.filter((varName) => !process.env[varName]);

if (missingEnvVars.length > 0) {
  throw new Error(`Missing required environment variables: ${missingEnvVars.join(', ')}`);
}

const { MONGO_USER, MONGO_PASSWORD, MONGO_HOST, MONGO_PORT, MONGO_DBNAME, REDIS_HOST, REDIS_PORT, REDIS_DB, NODE_ENV } =
  process.env;

const config = {
  username: MONGO_USER,
  password: MONGO_PASSWORD,
  database: MONGO_DBNAME,
  host: MONGO_HOST,
  port: MONGO_PORT,
  dialect: 'mongodb',
  redisPort: REDIS_PORT,
  redisHost: REDIS_HOST,
  redisDB: REDIS_DB,
  env: NODE_ENV,
};

export default config;
