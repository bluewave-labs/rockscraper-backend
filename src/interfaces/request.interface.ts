import { Request } from "express";

interface UserRequestInterface extends Request {
  user?: {
    role?: string;
    id?: string;
    email?: string;
  };
}

export default UserRequestInterface;
