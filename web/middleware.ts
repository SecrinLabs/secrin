import { NextResponse } from "next/server";
import { NextRequestWithAuth, withAuth } from "next-auth/middleware";

export default withAuth(
  function middleware(request: NextRequestWithAuth) {
    if (!request.nextauth.token) {
      // Return 404 response directly instead of a redirect
      return NextResponse.redirect(new URL("/404", request.url));
    }
    return NextResponse.next();
  },
  {
    pages: {
      // This prevents the default redirect to signin
      signIn: "/404",
    },
  }
);

export const config = {
  matcher: ["/connect/:path*", "/dashboard/:path*"],
};
