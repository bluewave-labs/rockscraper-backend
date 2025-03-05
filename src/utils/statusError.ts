import HTTP_STATUS_CODES from './httpCodes';

class StatusError extends Error {
  public statusCode: number;

  constructor(message: string, statusCode: number = HTTP_STATUS_CODES.INTERNAL_SERVER_ERROR) {
    super(message);
    this.statusCode = statusCode;
  }
}

export default StatusError;
