import mongoose from 'mongoose';
import config from './config';

const { database, host, password, port, username } = config;

const MONGO_URI = `mongodb://${username}:${password}@${host}:${port}/${database}?authSource=admin`;

const connection = async () => mongoose.connect(MONGO_URI);

export default connection;
