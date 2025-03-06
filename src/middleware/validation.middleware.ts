import { NextFunction, Request, Response } from 'express';
import { validationResult } from 'express-validator';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import { response } from '../utils/response.helper';

const handleValidationErrors = (req: Request, res: Response, next: NextFunction) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return response({
      res,
      status: HTTP_STATUS_CODES.BAD_REQUEST,
      error: errors
        .array()
        .map((err) => err.msg)
        .join(', '),
    });
  }
  next();
};

export { handleValidationErrors };
