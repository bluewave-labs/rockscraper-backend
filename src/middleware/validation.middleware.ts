import { NextFunction, Request, Response } from 'express';
import { validationResult } from 'express-validator';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import StatusError from '../utils/statusError';

const handleValidationErrors = (req: Request, res: Response, next: NextFunction) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    throw new StatusError(
      errors
        .array()
        .map((err) => err.msg)
        .join(', '),
      HTTP_STATUS_CODES.BAD_REQUEST
    );
  }
  next();
};

export { handleValidationErrors };
