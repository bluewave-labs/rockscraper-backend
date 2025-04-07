import { NextFunction, Response } from 'express';
import UserRequestInterface from '../interfaces/request.interface';
import Token from '../models/Token.model';
import User from '../models/User.model';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import { verifyToken } from '../utils/jwt.helper';
import StatusError from '../utils/statusError';

const { JWT_EXPIRATION_TIME } = process.env;

const authenticateJWT = async (req: UserRequestInterface, res: Response, next: NextFunction) => {
  const token = req.headers?.authorization?.split(' ')[1];
  if (!token) throw new StatusError('Token not provided', HTTP_STATUS_CODES.UNAUTHORIZED);

  try {
    const decoded = verifyToken(token);
    if (!decoded) throw new StatusError('Invalid token', HTTP_STATUS_CODES.UNAUTHORIZED);

    const dbToken = await Token.findOne({ where: { token, userId: decoded.id, type: 'auth' } });
    if (!dbToken) throw new StatusError('Invalid token', HTTP_STATUS_CODES.UNAUTHORIZED);

    const createdAt = new Date(dbToken.createdAt);
    const expiresAt = new Date(createdAt.getTime() + parseInt(JWT_EXPIRATION_TIME ?? '1', 10));
    if (new Date() > expiresAt) {
      await dbToken.destroy();
      throw new StatusError('Token expired', HTTP_STATUS_CODES.UNAUTHORIZED);
    }
    const user = await User.findOne({ where: { id: decoded.id } });
    if (!user) {
      throw new StatusError('User not found', HTTP_STATUS_CODES.NOT_FOUND);
    }
    req.user = {
      id: user.id,
      email: user.email,
      role: user.role,
    };
    next();
  } catch (error) {
    console.error('Error authenticating token:', error);
    throw new StatusError('Internal Server Error', HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR);
  }
};

module.exports = authenticateJWT;
