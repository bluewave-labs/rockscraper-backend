import dotenv from 'dotenv';
import mongoose from 'mongoose';

// load environment from the correct .env file based on the NODE_ENV variable (dev, prod, test)
dotenv.config({ path: `./.env.${process.env.NODE_ENV ?? 'dev'}` });

const requiredEnvVars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD'];
const missingEnvVars = requiredEnvVars.filter((varName) => !process.env[varName]);

if (missingEnvVars.length > 0) {
  throw new Error(`Missing required environment variables: ${missingEnvVars.join(', ')}`);
}

const { DB_PORT, DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME } = process.env;

const MONGO_URI = `mongodb://${DB_USERNAME}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?authSource=admin`;

const connection = async () => mongoose.connect(MONGO_URI);

export default connection;
