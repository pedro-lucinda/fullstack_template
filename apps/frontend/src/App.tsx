import { useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";

import { Button } from "@/components/ui/button";
import { setAccessTokenGetter } from "@/api/client";
import { TodosPage } from "@/pages/TodosPage";

export default function App() {
  const { isAuthenticated, isLoading, loginWithRedirect, logout, getAccessTokenSilently, user } =
    useAuth0();

  useEffect(() => {
    setAccessTokenGetter(async () => {
      try {
        return await getAccessTokenSilently();
      } catch {
        return undefined;
      }
    });
  }, [getAccessTokenSilently]);

  if (isLoading) {
    return <div className="p-8 text-center text-muted-foreground">Loading...</div>;
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <h1 className="text-2xl font-semibold">Fullstack Template</h1>
        <Button onClick={() => loginWithRedirect()}>Log in</Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-8">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Todos</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{user?.email}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
          >
            Log out
          </Button>
        </div>
      </header>
      <TodosPage />
    </div>
  );
}
