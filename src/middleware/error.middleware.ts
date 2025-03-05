/* eslint-disable no-unused-vars */
import { NextFunction, Request, Response } from 'express';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import StatusError from '../utils/statusError';

function errorMiddleware(error: Error, req: Request, res: Response, next: NextFunction) {
  if (error instanceof StatusError) {
    return res.status(error.statusCode).json({ success: false, data: null, error: error.message });
  }
  if (error instanceof SyntaxError) {
    console.error('JSON Syntax Error:', error);
    return res.status(400).json({ error: 'Invalid JSON format' });
  }
  console.log(error);
  return res
    .status(HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR)
    .json({ success: false, data: null, error: 'Internal Server Error' });
}

export default errorMiddleware;
