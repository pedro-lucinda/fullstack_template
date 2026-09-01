/**
 * Custom fetch client consumed by the Kubb-generated API functions
 * (see kubb.config.ts `importPath`). Type shapes match Kubb's built-in fetch
 * client contract so generated code type-checks against this module.
 * Attaches the Auth0 access token to every request and points at the backend
 * base URL.
 */

export type RequestCredentials = "omit" | "same-origin" | "include";

export type RequestConfig<TData = unknown> = {
  baseURL?: string;
  url?: string;
  method?: "GET" | "PUT" | "PATCH" | "POST" | "DELETE" | "OPTIONS" | "HEAD";
  params?: unknown;
  data?: TData | FormData;
  responseType?: "arraybuffer" | "blob" | "document" | "json" | "text" | "stream";
  signal?: AbortSignal;
  headers?: [string, string][] | Record<string, string>;
  credentials?: RequestCredentials;
};

export type ResponseConfig<TData = unknown> = {
  data: TData;
  status: number;
  statusText: string;
  headers: Headers;
};

export type ResponseErrorConfig<TError = unknown> = TError;

export type Client = <TData, _TError = unknown, TVariables = unknown>(
  config: RequestConfig<TVariables>
) => Promise<ResponseConfig<TData>>;

import { env } from "@/lib/env";

const BASE_URL = env.apiBaseUrl;

let accessTokenGetter: (() => Promise<string | undefined>) | undefined;

/** Called once from the app root (see src/App.tsx) so the API client can
 * retrieve a fresh Auth0 access token for each request. */
export function setAccessTokenGetter(getter: () => Promise<string | undefined>) {
  accessTokenGetter = getter;
}

function headersToRecord(
  headers?: [string, string][] | Record<string, string>
): Record<string, string> {
  if (!headers) return {};
  return Array.isArray(headers) ? Object.fromEntries(headers) : headers;
}

export const client: Client = async <TData, _TError = unknown, TVariables = unknown>(
  config: RequestConfig<TVariables>
): Promise<ResponseConfig<TData>> => {
  const normalizedParams = new URLSearchParams();
  Object.entries((config.params as Record<string, unknown>) || {}).forEach(([key, value]) => {
    if (value !== undefined) {
      normalizedParams.append(key, value === null ? "null" : String(value));
    }
  });

  const base = config.baseURL ?? BASE_URL;
  let targetUrl = [base, config.url].filter(Boolean).join("");
  if (config.params) {
    targetUrl += `?${normalizedParams}`;
  }

  const token = await accessTokenGetter?.();

  const response = await globalThis.fetch(targetUrl, {
    credentials: config.credentials || "same-origin",
    method: config.method?.toUpperCase(),
    body: config.data instanceof FormData ? config.data : JSON.stringify(config.data),
    signal: config.signal,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headersToRecord(config.headers),
    },
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`API request failed (${response.status}): ${body}`);
  }

  const data =
    [204, 205, 304].includes(response.status) || !response.body
      ? ({} as TData)
      : ((await response.json()) as TData);

  return {
    data,
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  };
};

export default client;
