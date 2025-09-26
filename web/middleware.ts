import { NextResponse } from "next/server";
import { NextRequestWithAuth, withAuth } from "next-auth/middleware";
import { jwtDecode } from "jwt-decode"; // Changed: use named import instead of default import

export default withAuth(
  function middleware(request: NextRequestWithAuth) {
    const token = request.nextauth.token;

    // No token → redirect to login
    if (!token) {
      return NextResponse.redirect(new URL("/auth/login", request.url));
    }

    try {
      // Decode the JWT from NextAuth session
      const accessToken = token.accessToken as string;
      if (!accessToken) {
        return NextResponse.redirect(new URL("/auth/login", request.url));
      }

      const payload: { exp: number } = jwtDecode(accessToken);
      const now = Date.now() / 1000;

      // Token expired → redirect to login
      if (payload.exp < now) {
        return NextResponse.redirect(new URL("/auth/login", request.url));
      }
    } catch {
      // Invalid token → redirect to login
      return NextResponse.redirect(new URL("/auth/login", request.url));
    }

    // Token valid → continue
    return NextResponse.next();
  },
  {
    pages: {
      signIn: "/auth/login", // default login page
    },
  }
);

export const config = {
  matcher: [
    "/connect/:path*",
    "/channel/:path*",
    "/source/:path*",
    "/chat/:path*",
  ],
};
