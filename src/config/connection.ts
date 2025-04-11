import { Sequelize } from 'sequelize';
import config from './config';

const { database, host, password, port, username } = config;

[database, host, password, port, username].forEach((envVar) => {
  if (!envVar) {
    throw new Error('Missing required environment variables');
  }
});

const sequelize = new Sequelize({
  dialect: 'postgres',
  host,
  port: Number(port),
  username,
  password,
  database,
  logging: false,
  define: {
    timestamps: true,
    underscored: true,
  },
});

const connection = async () => {
  try {
    await sequelize.authenticate();
    console.log('PostgreSQL connection has been established successfully.');
    return sequelize;
  } catch (error) {
    console.error('Unable to connect to the PostgreSQL database:', error);
    throw error;
  }
};

export { sequelize };
export default connection;
