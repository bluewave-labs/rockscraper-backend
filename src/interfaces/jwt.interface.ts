import { JwtPayload } from 'jsonwebtoken';

interface JwtDecodeInterface extends JwtPayload {
  id: string;
  email: string;
  role: string;
}

export default JwtDecodeInterface;
