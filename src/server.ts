import cors from 'cors';
import express from 'express';
import helmet from 'helmet';
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
  await redis.ping((err, result) => {
    if (!err && result === 'PONG') {
      redisMsg = 'Redis is connected.';
    }
  });
  res.send(`${serverMsg} \n ${redisMsg}`);
});

app.use(errorMiddleware);

export default app;
