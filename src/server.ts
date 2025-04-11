import cors from 'cors';
import express from 'express';
import helmet from 'helmet';
import connection from './config/connection';
import redis from './config/redis';
import errorMiddleware from './middleware/error.middleware';
import constantsHelper from './utils/constants.helper';
import { sequelize } from './config/connection';

const { MAX_FILE_SIZE } = constantsHelper;

const app = express();
app.use(cors());
app.options('*', cors()); // this is for preflight requests
app.use(helmet());
app.use(express.json({ limit: MAX_FILE_SIZE }));

// Database connection and sync
sequelize
  .authenticate()
  .then(() => console.log("Database connected..."))
  .catch((err) => console.log("Error: " + err));

if (process.env.NODE_ENV === 'development') {
  sequelize
    .sync({ alter: true })
    .then(() => console.log("Models synced with the database..."))
    .catch((err) => console.log("Error syncing models: " + err));
}

app.get('/api/health', async (req, res) => {
  const serverMsg = 'Server is up and running.';
  let redisMsg = 'Redis is not connected.';
  let postgresMsg = 'PostgreSQL is not connected.';
  
  await redis.ping((err, result) => {
    if (!err && result === 'PONG') {
      redisMsg = 'Redis is connected.';
    }
  });
  
  try {
    await sequelize.authenticate();
    postgresMsg = 'PostgreSQL is connected.';
  } catch (error: any) {
    postgresMsg = `PostgreSQL connection error: ${error.message}`;
  }
  
  res.send(`${serverMsg} \n ${redisMsg} \n ${postgresMsg}`);
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
