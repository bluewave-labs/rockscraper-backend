/* eslint-disable no-unused-vars */
import { ErrorRequestHandler } from 'express';
import config from '../config/config';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import { response } from '../utils/response.helper';
import StatusError from '../utils/statusError';

const { env } = config;

const errorMiddleware: ErrorRequestHandler = (error, req, res, next) => {
  console.error(`${req.method} ${req.path} - Error:`, error);
  if (error instanceof StatusError) {
    response({ res, status: error.statusCode, error: error.message });
  }
  if (error instanceof SyntaxError) {
    response({ res, status: HTTP_STATUS_CODES.BAD_REQUEST, error: 'Invalid JSON payload passed.' });
    return;
  }
  if (error.name === 'ValidationError') {
    const messages = Object.values(error.errors).map((err: any) => err.message);
    response({ res, status: HTTP_STATUS_CODES.BAD_REQUEST, error: messages.join(', ') });
    return;
  }
  if (env === 'development') {
    response({ res, status: HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR, error: error.message });
    return;
  }
  response({ res, status: HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR, error: 'Internal Server Error' });
};

export default errorMiddleware;
