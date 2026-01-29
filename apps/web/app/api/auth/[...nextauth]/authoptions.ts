import { Session, User } from "next-auth";
import { JWT } from "next-auth/jwt";
import GitHubProvider from "next-auth/providers/github";
import { PrismaAdapter } from "@next-auth/prisma-adapter";
import { prisma } from "@/lib/prisma";

import { AdapterUser } from "@/types/next-auth";

export const authOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GitHubProvider({
      clientId: process.env.GITHUB_ID as string,
      clientSecret: process.env.GITHUB_SECRET as string,
    }),
  ],
  session: {
    strategy: "jwt" as const,
  },
  pages: {
    signIn: "/auth/login",
    newUser: "/onboarding", // Redirect to onboarding if new user
  },
  callbacks: {
    async jwt({ token, user, trigger, session }: { token: JWT; user?: User | AdapterUser; trigger?: "signIn" | "signUp" | "update"; session?: any }) {
      if (user) {
        token.id = user.id;
        token.isNew = (user as any).isNew;
      }
      
      // Update token if session is updated
      if (trigger === "update" && session?.isNew !== undefined) {
        token.isNew = session.isNew;
      }
      
      return token;
    },
    async session({ session, token }: { session: Session; token: JWT }) {
      if (session.user) {
        session.user.id = token.id as string;
        (session.user as any).isNew = token.isNew as boolean;
      }
      return session;
    },
  },
};
