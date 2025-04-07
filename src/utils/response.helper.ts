import ResponseInterface from '../interfaces/response.interface';

export function response({ res, data = null, status = 200, error = '' }: ResponseInterface) {
  res.status(status).json({ success: status < 400, data, error });
}
