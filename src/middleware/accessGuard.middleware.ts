import { NextFunction, Response } from 'express';
import UserRequestInterface from '../interfaces/request.interface';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import StatusError from '../utils/statusError';

const accessGuard = (permissions: string[]) => {
  return (req: UserRequestInterface, res: Response, next: NextFunction) => {
    if (!req?.user?.role || !permissions.includes(req.user.role)) {
      throw new StatusError('User does not have required access level', HTTP_STATUS_CODES.FORBIDDEN);
    }
    next();
  };
};

export default accessGuard;
