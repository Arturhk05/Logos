// The largest id the API accepts (a PostgreSQL INTEGER); a larger one would only come back as invalid.
const MAX_INCIDENT_ID = 2_147_483_647;

/** The incident id in the URL, or null when it is missing or could not be an incident. */
export function parseIncidentId(value: string | undefined): number | null {
  if (value === undefined || !/^\d+$/.test(value)) return null;
  const id = Number(value);
  return id >= 1 && id <= MAX_INCIDENT_ID ? id : null;
}
