import { NextFunction, Request, Response } from 'express';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import { response } from '../utils/response.helper';

const { MAX_FILE_SIZE } = require('../utils/constants.helper');

const fileSizeValidator = (req: Request, res: Response, next: NextFunction) => {
  if (req.method !== 'POST' && req.method !== 'PUT') {
    return next();
  }
  const contentLength = Number(req.headers['content-length']);

  if (isNaN(contentLength)) {
    return response({ res, status: HTTP_STATUS_CODES.BAD_REQUEST, error: 'Invalid content length' });
  }

  if (contentLength > MAX_FILE_SIZE) {
    return response({
      res,
      status: HTTP_STATUS_CODES.PAYLOAD_TOO_LARGE,
      error: `File size exceeds the limit of ${MAX_FILE_SIZE} bytes`,
    });
  }

  next();
};

export default fileSizeValidator;
