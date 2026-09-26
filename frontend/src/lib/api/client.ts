import type { ErrorResponse } from "./types";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

/** An error returned by the Burhan API, or a network failure reaching it. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
    public readonly details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isNetworkError(): boolean {
    return this.status === 0;
  }
}

type Query = Record<string, string | number | boolean | string[] | undefined | null>;

export function buildUrl(path: string, query?: Query): string {
  const url = new URL(`${API_BASE_URL}/api${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === "") continue;
    for (const v of Array.isArray(value) ? value : [value]) url.searchParams.append(key, String(v));
  }
  return url.toString();
}

async function parseError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    if (body?.error) {
      const { code, message, details } = (body as ErrorResponse).error;
      return new ApiError(message, res.status, code, details ?? {});
    }
    if (body?.detail) {
      // FastAPI request-validation errors
      const detail = Array.isArray(body.detail)
        ? body.detail.map((d: { msg?: string }) => d.msg).join("; ")
        : String(body.detail);
      return new ApiError(detail, res.status, "validation_error");
    }
  } catch {
    /* non-JSON body */
  }
  return new ApiError(res.statusText || "Request failed", res.status, "http_error");
}

export async function request<T>(
  path: string,
  init: RequestInit & { query?: Query } = {},
): Promise<T> {
  const { query, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), {
      ...rest,
      headers: { Accept: "application/json", ...rest.headers },
    });
  } catch {
    throw new ApiError(
      `Cannot reach the Burhan API at ${API_BASE_URL}. Is the backend running?`,
      0,
      "network_error",
    );
  }
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}
