interface TokenInterface {
  id?: string;
  token: string;
  userId: string;
  type: string;
  createdAt: Date;
  destroy: () => Promise<void>;
}

export default TokenInterface;
