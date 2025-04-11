import dotenv from 'dotenv';
import connection from './config/connection';
import api from './server';
import { sequelize } from './config/connection';
dotenv.config();

const PORT = process.env.PORT ?? 3000;

const startServer = async () => {
  try {
    // Connect to the database
    await connection();
    
    // Sync database models
    await sequelize.sync({ alter: process.env.NODE_ENV === 'dev' });
    console.log('Database models synchronized');
    
    // Start the server
    api.listen(PORT, () => {
      console.log(`Server listening on port ${PORT}`);
    });
  } catch (error) {
    console.error('Error starting server: ', error);
    process.exit(1);
  }
};

startServer();
