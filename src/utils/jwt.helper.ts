import 'dotenv/config';
import jwt, { JwtPayload } from 'jsonwebtoken';
import JwtDecodeInterface from '../interfaces/jwt.interface';
import constantsHelper from './constants.helper';
import HTTP_STATUS_CODES from './httpCodes';
import StatusError from './statusError';

const { JWT_EXPIRES_IN_1H } = constantsHelper;
const { JWT_SECRET } = process.env;

const generateToken = (payload: JwtPayload, expiresIn = JWT_EXPIRES_IN_1H) => {
  if (!JWT_SECRET) {
    throw new StatusError('JWT_SECRET not set', HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR);
  }
  return jwt.sign(payload, JWT_SECRET, { expiresIn });
};

const verifyToken: (token: string) => JwtDecodeInterface = (token: string) => {
  try {
    if (!JWT_SECRET) {
      throw new StatusError('JWT_SECRET not set', HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR);
    }
    return jwt.verify(token, JWT_SECRET) as JwtDecodeInterface;
  } catch (error) {
    throw new StatusError('Invalid token', HTTP_STATUS_CODES.FORBIDDEN);
  }
};

export { generateToken, verifyToken };
