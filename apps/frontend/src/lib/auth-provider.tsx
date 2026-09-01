import type { ReactNode } from "react";
import { Auth0Provider } from "@auth0/auth0-react";

import { env } from "@/lib/env";

const domain = env.auth0Domain;
const clientId = env.auth0ClientId;
const audience = env.auth0Audience;

/**
 * Wraps the app with Auth0's React SDK. Configure via VITE_AUTH0_DOMAIN,
 * VITE_AUTH0_CLIENT_ID, and VITE_AUTH0_AUDIENCE environment variables.
 */
export function AppAuthProvider({ children }: { children: ReactNode }) {
  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience,
      }}
      cacheLocation="localstorage"
      useRefreshTokens
    >
      {children}
    </Auth0Provider>
  );
}
