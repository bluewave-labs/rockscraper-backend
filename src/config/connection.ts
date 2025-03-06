import mongoose from 'mongoose';
import config from './config';

const { database, host, password, port, username } = config;

[database, host, password, port, username].forEach((envVar) => {
  if (!envVar) {
    throw new Error('Missing required environment variables');
  }
});

const MONGO_URI = `mongodb://${encodeURIComponent(username as string)}:${encodeURIComponent(
  password as string
)}@${host}:${port}/${database}?authSource=admin`;

const connection = async () => mongoose.connect(MONGO_URI);

export default connection;
