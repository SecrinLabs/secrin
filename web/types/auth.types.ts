export interface PasswordCheckRequest {
  token: string;
  password: string;
}

export interface PasswordCheckResponse {
  user: {
    email: string;
  };
}

export interface UserLoginRequest {
  email: string;
  password: string;
}
