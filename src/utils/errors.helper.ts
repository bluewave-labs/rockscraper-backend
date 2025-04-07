import { ErrorHelperInterface } from '../interfaces/error.interface';
import { STATUS_CODES } from 'http';
const GENERAL_ERROR_CODE = '099';

function errorResponse(statusCode: number, errorCode: string, message: null | undefined | string) {
  const payload: ErrorHelperInterface = { error: STATUS_CODES[statusCode] ?? 'Unknown error' };
  if (message) {
    payload.message = message;
  }
  if (errorCode) {
    payload.errorCode = errorCode;
  }
  return {
    statusCode,
    payload,
  };
}

function badRequest(message: string, errorCode = GENERAL_ERROR_CODE) {
  return errorResponse(400, errorCode, message);
}

function internalServerError(errorCode: string, message = null) {
  return errorResponse(500, errorCode, message);
}

export { badRequest, errorResponse, internalServerError };
