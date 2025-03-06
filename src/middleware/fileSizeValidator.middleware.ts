import { NextFunction, Request, Response } from 'express';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import StatusError from '../utils/statusError';

const { MAX_FILE_SIZE } = require('../utils/constants.helper');

const fileSizeValidator = (req: Request, res: Response, next: NextFunction) => {
  if (req.method !== 'POST' && req.method !== 'PUT') {
    return next();
  }
  const contentLength = Number(req.headers['content-length']);

  if (isNaN(contentLength)) {
    throw new StatusError('Invalid content length', HTTP_STATUS_CODES.BAD_REQUEST);
  }

  if (contentLength > MAX_FILE_SIZE) {
    throw new StatusError(`File size exceeds the limit of ${MAX_FILE_SIZE} bytes`, HTTP_STATUS_CODES.PAYLOAD_TOO_LARGE);
  }

  next();
};

export default fileSizeValidator;
