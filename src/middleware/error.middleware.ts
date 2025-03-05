/* eslint-disable no-unused-vars */
import { ErrorRequestHandler } from 'express';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import StatusError from '../utils/statusError';

const errorMiddleware: ErrorRequestHandler = (error, req, res, next) => {
  if (error instanceof StatusError) {
    res.status(error.statusCode).json({ success: false, data: null, error: error.message });
    return;
  }
  if (error instanceof SyntaxError) {
    console.error('JSON Syntax Error:', error);
    res.status(400).json({ error: 'Invalid JSON format' });
    return;
  }
  console.log(error);
  res
    .status(HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR)
    .json({ success: false, data: null, error: 'Internal Server Error' });
};

export default errorMiddleware;
