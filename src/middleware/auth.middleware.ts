import { NextFunction, Response } from 'express';
import UserRequestInterface from '../interfaces/request.interface';
import Token from '../models/Token.model';
import User from '../models/User.model';
import HTTP_STATUS_CODES from '../utils/httpCodes';
import { verifyToken } from '../utils/jwt.helper';
import { response } from '../utils/response.helper';

const { JWT_EXPIRATION_TIME } = process.env;

const authenticateJWT = async (req: UserRequestInterface, res: Response, next: NextFunction) => {
  const token = req.headers?.authorization?.split(' ')[1];
  if (!token) return response({ res, status: HTTP_STATUS_CODES.UNAUTHORIZED, error: 'Token not provided' });

  try {
    const decoded = verifyToken(token);
    if (!decoded) return response({ res, status: HTTP_STATUS_CODES.UNAUTHORIZED, error: 'Invalid token' });

    const dbToken = await Token.findOne({ where: { token, userId: decoded.id, type: 'auth' } });
    if (!dbToken) return response({ res, status: HTTP_STATUS_CODES.UNAUTHORIZED, error: 'Invalid token' });

    const createdAt = new Date(dbToken.createdAt);
    const expiresAt = new Date(createdAt.getTime() + parseInt(JWT_EXPIRATION_TIME ?? '1', 10));
    if (new Date() > expiresAt) {
      await dbToken.destroy();
      return response({ res, status: HTTP_STATUS_CODES.UNAUTHORIZED, error: 'Token expired' });
    }
    const user = await User.findOne({ where: { id: decoded.id } });
    if (!user) {
      return response({ res, status: HTTP_STATUS_CODES.NOT_FOUND, error: 'User not found' });
    }
    req.user = {
      id: user.id,
      email: user.email,
      role: user.role,
    };
    next();
  } catch (error) {
    console.error('Error authenticating token:', error);
    return response({ res, status: HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR, error: 'Internal Server Error' });
  }
};

module.exports = authenticateJWT;
