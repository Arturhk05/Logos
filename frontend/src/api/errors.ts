import type { IncidentDetail } from "./client";

export type ApiErrorKind =
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "invalid"
  | "rate_limited"
  | "unavailable"
  | "server"
  | "network"
  | "timeout";

// Used when the response has no message of its own, e.g. the HTML error page of CloudFront.
const DEFAULT_MESSAGES: Record<ApiErrorKind, string> = {
  unauthorized: "Sua sessão expirou. Entre novamente.",
  forbidden: "Você não tem permissão para esta ação.",
  not_found: "Não encontramos o que você procurava.",
  conflict: "Este incidente foi alterado por outra pessoa. Confira como ele está agora.",
  invalid: "Dados inválidos. Revise os campos e tente novamente.",
  rate_limited: "Muitas tentativas seguidas. Aguarde um pouco e tente novamente.",
  unavailable: "O sistema está temporariamente indisponível. Tente novamente em instantes.",
  server: "Ocorreu um erro inesperado. Tente novamente em instantes.",
  network: "Sem conexão. Verifique sua internet e tente novamente.",
  timeout: "O sistema demorou para responder. Tente novamente.",
};

const KIND_BY_STATUS = new Map<number, ApiErrorKind>([
  [401, "unauthorized"],
  [403, "forbidden"],
  [404, "not_found"],
  [409, "conflict"],
  [422, "invalid"],
  [429, "rate_limited"],
  [502, "unavailable"],
  [503, "unavailable"],
  [504, "unavailable"],
]);

interface ApiErrorOptions {
  status?: number;
  message?: string;
  retryAfterSeconds?: number;
  current?: IncidentDetail;
}

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | undefined;
  readonly retryAfterSeconds: number | undefined;
  readonly current: IncidentDetail | undefined;

  constructor(kind: ApiErrorKind, options: ApiErrorOptions = {}) {
    super(options.message ?? DEFAULT_MESSAGES[kind]);
    this.name = "ApiError";
    this.kind = kind;
    this.status = options.status;
    this.retryAfterSeconds = options.retryAfterSeconds;
    this.current = options.current;
  }

  // The body is checked at runtime: the OpenAPI types declare a list as the 422 detail, but the API sends text.
  static fromResponse(response: Response, body: unknown): ApiError {
    const knownKind = KIND_BY_STATUS.get(response.status);
    const kind = knownKind ?? "server";
    const fields: Record<string, unknown> = isRecord(body) ? body : {};
    const detail = fields.detail;
    // Other statuses come from the framework or a proxy (e.g. 405 "Method Not Allowed"), in English.
    const useDetail = knownKind !== undefined && typeof detail === "string" && detail.trim() !== "";
    return new ApiError(kind, {
      status: response.status,
      message: useDetail ? detail : undefined,
      retryAfterSeconds:
        kind === "rate_limited" ? parseRetryAfter(response.headers.get("Retry-After")) : undefined,
      current:
        kind === "conflict" && isRecord(fields.current)
          ? (fields.current as IncidentDetail)
          : undefined,
    });
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// The API sends seconds; the HTTP-date form is ignored rather than trusting the client clock.
function parseRetryAfter(header: string | null): number | undefined {
  const value = header?.trim();
  return value !== undefined && /^\d+$/.test(value) ? Number(value) : undefined;
}
