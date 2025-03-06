import Redis from 'ioredis';
import config from './config';

const { redisDB, redisHost, redisPort } = config;

const redis = new Redis(parseInt(redisPort ?? '6379'), redisHost ?? 'localhost', {
  db: parseInt(redisDB ?? '0'),
});

redis.on('error', (error) => {
  console.error('Redis connection error:', error);
});

redis.on('connect', () => {
  console.log('Connected to Redis');
});

// Handle graceful shutdown
process.on('SIGINT', async () => {
  await redis.quit();
  console.log('Redis connection closed');
  process.exit(0);
});

export default redis;
