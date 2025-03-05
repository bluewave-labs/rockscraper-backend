interface UserRequestInterface extends Request {
  user?: {
    role?: string;
    id?: string;
    email?: string;
  };
  headers: Headers & {
    authorization?: string;
  };
}

export default UserRequestInterface;
