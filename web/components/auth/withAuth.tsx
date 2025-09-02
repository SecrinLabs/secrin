import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { FC, ComponentType } from "react";

export function withAuth<P extends object>(
  WrappedComponent: ComponentType<P>
): FC<P> {
  return function ProtectedComponent(props: P) {
    const { data: session, status } = useSession();

    if (status === "loading") {
      return <div>Loading...</div>;
    }

    if (!session) {
      redirect("/auth/login");
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}
