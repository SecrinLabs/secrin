import { Session, User } from "next-auth";
import { JWT } from "next-auth/jwt";
import CredentialsProvider from "next-auth/providers/credentials";

import { loginUser, AuthApiError } from "@/service/auth";
import { AdapterUser } from "@/types/next-auth";

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: {
          label: "Email",
          type: "text",
          placeholder: "john@example.com",
        },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Email and password are required");
        }

        try {
          const response = await loginUser({
            email: credentials.email,
            password: credentials.password,
          });

          if (response.data.access_token) {
            return {
              ...response.data.user,
              accessToken: response.data.access_token, // <- save JWT
            };
          }

          return null;
        } catch (error: unknown) {
          console.error("Login error:", error);
          if (error instanceof AuthApiError) {
            throw new Error(error.message);
          }
          throw new Error("An unexpected error occurred during login");
        }
      },
    }),
  ],
  session: {
    strategy: "jwt" as const,
  },
  callbacks: {
    async jwt({ token, user }: { token: JWT; user?: AdapterUser | User }) {
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.username = user.username;
        token.userGUID = user.userGUID;
        token.isUserPro = user.isUserPro;
        token.accessToken = user.accessToken;
      }
      return token;
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (session.user) {
        session.user.id = token.id;
        session.user.email = token.email;
        session.user.username = token.username;
        session.user.userGUID = token.userGUID;
        session.user.isUserPro = token.isUserPro;
      }
      session.accessToken = token.accessToken;
      return session;
    },
  },
};
