const MINUTE_MS = 60_000;
const HOUR_MS = 60 * MINUTE_MS;
const DAY_MS = 24 * HOUR_MS;

/** How long ago something happened, in the short form shown in lists ("3 min", "2 h", "1 dia"). */
export function formatElapsed(createdAt: string, now: Date): string {
  const elapsed = now.getTime() - new Date(createdAt).getTime();
  if (elapsed < MINUTE_MS) return "agora";
  if (elapsed < HOUR_MS) return `${String(Math.floor(elapsed / MINUTE_MS))} min`;
  if (elapsed < DAY_MS) return `${String(Math.floor(elapsed / HOUR_MS))} h`;
  const days = Math.floor(elapsed / DAY_MS);
  return days === 1 ? "1 dia" : `${String(days)} dias`;
}

/** Date and time in pt-BR, with the year only when it is not the current one. */
export function formatDateTime(value: string, now: Date, timeZone?: string): string {
  const date = new Date(value);
  const sameYear =
    date.toLocaleString("en", { year: "numeric", timeZone }) ===
    now.toLocaleString("en", { year: "numeric", timeZone });
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: sameYear ? undefined : "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  }).format(date);
}
