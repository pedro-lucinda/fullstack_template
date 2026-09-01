/**
 * Central place for Vite environment variables. Isolated in its own module so
 * it can be swapped out with a plain mock in Jest (which doesn't understand
 * `import.meta.env`) via moduleNameMapper — see jest.config.ts.
 */
export const env = {
  auth0Domain: import.meta.env.VITE_AUTH0_DOMAIN as string,
  auth0ClientId: import.meta.env.VITE_AUTH0_CLIENT_ID as string,
  auth0Audience: import.meta.env.VITE_AUTH0_AUDIENCE as string,
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000",
};
