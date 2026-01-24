import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/authoptions";
import { redirect } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { LogoutButton } from "@/components/logout-button";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/auth/login");
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-2xl">Dashboard</CardTitle>
          <CardDescription>Authorized Access Area</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4 rounded-md border p-4">
            {session?.user?.image && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={session.user.image}
                alt={session.user.name || "User Avatar"}
                className="h-16 w-16 rounded-full border-2 border-primary"
              />
            )}
            <div>
              <h3 className="text-lg font-medium">
                {session?.user?.name || "No Name"}
              </h3>
              <p className="text-sm text-muted-foreground">
                {session?.user?.email || "No Email"}
              </p>
              {session?.user?.id && (
                <p className="text-xs text-muted-foreground mt-1">
                  User ID: {session.user.id}
                </p>
              )}
            </div>
          </div>

          <div className="rounded-md bg-muted p-4">
            <h4 className="mb-2 font-medium">Verified Account Information:</h4>
            <p className="text-sm text-muted-foreground mb-2">
              The detailed information below confirms this session is
              authenticated via GitHub.
            </p>
            <div className="bg-background rounded border p-2 text-xs font-mono overflow-auto max-h-48">
              {JSON.stringify(session, null, 2)}
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between items-center">
          <p className="text-sm text-muted-foreground">Securely logged in</p>
          <LogoutButton />
        </CardFooter>
      </Card>
    </div>
  );
}
