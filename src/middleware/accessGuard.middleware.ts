import { NextFunction, Response } from 'express';
import UserRequestInterface from '../interfaces/request.interface';

const accessGuard = (permissions: string[]) => {
  return (req: UserRequestInterface, res: Response, next: NextFunction) => {
    if (!req?.user?.role || !permissions.includes(req.user.role)) {
      return res.status(403).json({ error: 'User does not have required access level' });
    }
    next();
  };
};

export default accessGuard;
