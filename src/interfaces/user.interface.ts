interface UserInterface {
  id?: string;
  email: string;
  password: string;
  role: string;
  createdAt: Date;
  updatedAt: Date;
}

export default UserInterface;
