import { NextFunction, Response } from 'express';
import UserRequestInterface from '../interfaces/request.interface';
import Token from '../models/Token.model';
import User from '../models/User.model';
import { verifyToken } from '../utils/jwt.helper';

const { JWT_EXPIRATION_TIME } = process.env;

const authenticateJWT = async (req: UserRequestInterface, res: Response, next: NextFunction) => {
  const token = req.headers?.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });

  try {
    const decoded = verifyToken(token);
    if (!decoded) return res.status(401).json({ error: 'Invalid token' });

    const dbToken = await Token.findOne({ where: { token, userId: decoded.id, type: 'auth' } });
    if (!dbToken) return res.status(401).json({ error: 'Invalid token' });

    const createdAt = new Date(dbToken.createdAt);
    const expiresAt = new Date(createdAt.getTime() + parseInt(JWT_EXPIRATION_TIME ?? '1', 10));
    if (new Date() > expiresAt) {
      await dbToken.destroy();
      return res.status(401).json({ error: 'Token has expired' });
    }
    const user = await User.findOne({ where: { id: decoded.id } });
    if (!user) {
      return res.status(404).json('User not found');
    }
    req.user = {
      id: user.id,
      email: user.email,
      role: user.role,
    };
    next();
  } catch (error) {
    console.error('Error authenticating token:', error);
    return res.status(500).json({ error: 'Internal Server Error' });
  }
};

module.exports = authenticateJWT;
