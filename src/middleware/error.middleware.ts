/* eslint-disable no-unused-vars */
import { ErrorRequestHandler } from 'express';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import StatusError from '../utils/statusError';
import config from '../config/config';

const { env } = config;

const errorMiddleware: ErrorRequestHandler = (error, req, res, next) => {
  console.error(`${req.method} ${req.path} - Error:`, error);
  if (error instanceof StatusError) {
    res.status(error.statusCode).json({ success: false, data: null, error: error.message });
    return;
  }
  if (error instanceof SyntaxError) {
    res.status(400).json({ success: false, data: null, error: 'Invalid JSON format' });
    return;
  }
  if (error.name === 'ValidationError') {
    const messages = Object.values(error.errors).map((err: any) => err.message);
    res.status(400).json({ success: false, data: null, error: messages.join(', ') });
    return;
  }
  if (env === 'development') {
    res.status(HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR).json({
      success: false,
      data: null,
      error: 'Internal Server Error',
      stack: error.stack,
    });
    return;
  }
  res
    .status(HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR)
    .json({ success: false, data: null, error: 'Internal Server Error' });
};

export default errorMiddleware;
