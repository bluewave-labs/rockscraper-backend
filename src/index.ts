import dotenv from 'dotenv';
import connection from './config/connection';
import api from './server';
dotenv.config();

const PORT = process.env.PORT ?? 3000;

connection()
  .then(() => {
    api.listen(PORT, () => {
      console.log(`Server listening on port ${PORT}`);
    });
  })
  .catch((error) => {
    console.error('Error starting server: ', error);
    process.exit(1);
  });
