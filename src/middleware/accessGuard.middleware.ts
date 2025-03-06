import { NextFunction, Response } from 'express';
import UserRequestInterface from '../interfaces/request.interface';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import { response } from '../utils/response.helper';

const accessGuard = (permissions: string[]) => {
  return (req: UserRequestInterface, res: Response, next: NextFunction) => {
    if (!req?.user?.role || !permissions.includes(req.user.role)) {
      return response({
        res,
        status: HTTP_STATUS_CODES.FORBIDDEN,
        error: 'User does not have required access level',
      });
    }
    next();
  };
};

export default accessGuard;
