import { Response } from 'express';

interface ResponseInterface {
  res: Response;
  data?: any;
  status?: number;
  error?: string;
}

export default ResponseInterface;
