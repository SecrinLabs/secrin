// next-auth.d.ts
import { DefaultSession, User } from "next-auth";

declare module "next-auth" {
  interface Session extends DefaultSession {
    user: {
      id: string; // always string
      email?: string;
      username?: string;
      userGUID?: string;
      isUserPro?: boolean;
    } & DefaultSession["user"];
    accessToken: JWT;
  }

  interface User {
    id: string;
    email?: string;
    username?: string;
    userGUID?: string;
    isUserPro?: boolean;
    accessToken: JWT;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    email?: string;
    username?: string;
    userGUID?: string;
    isUserPro?: boolean;
  }
}

export interface AdapterUser extends User {
  id: string;
}
