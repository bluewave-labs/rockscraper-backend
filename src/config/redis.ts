import Redis from 'ioredis';
import config from './config';

const { redisDB, redisHost, redisPort } = config;

const redis = new Redis(parseInt(redisPort ?? '6379'), redisHost ?? 'localhost', {
  db: parseInt(redisDB ?? '0'),
});

export default redis;
