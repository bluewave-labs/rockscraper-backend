import cors from 'cors';
import express, { ErrorRequestHandler } from 'express';
import helmet from 'helmet';
import errorMiddleware from './middleware/error.middleware';
import constantsHelper from './utils/constants.helper';

const { MAX_FILE_SIZE } = constantsHelper;

const app = express();
app.use(cors());
app.options('*', cors()); // this is for preflight requests
app.use(helmet());
app.use(express.json({ limit: MAX_FILE_SIZE }));

app.use(errorMiddleware as unknown as ErrorRequestHandler);

export default app;
