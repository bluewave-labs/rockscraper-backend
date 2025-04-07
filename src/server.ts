import cors from 'cors';
import express from 'express';
import helmet from 'helmet';
import connection from './config/connection';
import redis from './config/redis';
import errorMiddleware from './middleware/error.middleware';
import constantsHelper from './utils/constants.helper';

const { MAX_FILE_SIZE } = constantsHelper;

const app = express();
app.use(cors());
app.options('*', cors()); // this is for preflight requests
app.use(helmet());
app.use(express.json({ limit: MAX_FILE_SIZE }));

app.get('/api/health', async (req, res) => {
  const serverMsg = 'Server is up and running.';
  let redisMsg = 'Redis is not connected.';
  let mongoMsg = 'MongoDB is not connected.';
  await redis.ping((err, result) => {
    if (!err && result === 'PONG') {
      redisMsg = 'Redis is connected.';
    }
  });
  try {
    const mongoose = (await connection()).connection;
    if (mongoose.readyState === 1) {
      mongoMsg = 'MongoDB is connected.';
    }
  } catch (error: any) {
    mongoMsg = `MongoDB connection error: ${error.message}`;
  }
  res.send(`${serverMsg} \n ${redisMsg} \n ${mongoMsg}`);
});

app.use(errorMiddleware);

app.use((req, res) => {
  res.status(404).json({
    success: false,
    data: null,
    error: `Route ${req.method} ${req.originalUrl} not found`,
  });
});

export default app;
