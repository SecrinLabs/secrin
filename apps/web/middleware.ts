import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware(req) {
    // If not authenticated, the default middleware handles redirection to signin
    
    // Check if user is new and trying to access dashboard
    const isNew = (req.nextauth.token as any)?.isNew;
    const isOnboarding = req.nextUrl.pathname.startsWith("/onboarding");
    const isDashboard = req.nextUrl.pathname.startsWith("/dashboard");

    // If user is new and trying to access dashboard (or any protected route other than onboarding)
    // Redirect to onboarding
    if (isNew && !isOnboarding && isDashboard) {
      return NextResponse.redirect(new URL("/onboarding", req.url));
    }

    // If user is NOT new but tries to access onboarding
    // Redirect to dashboard
    if (!isNew && isOnboarding) {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
  }
);

export const config = { matcher: ["/dashboard/:path*", "/onboarding"] };
