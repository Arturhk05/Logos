import {
  CATEGORIES,
  CRITICALITIES,
  type Criticality,
  type IncidentCategory,
} from "../../shared/labels";

/** Filters shared by the queue and the history, kept in the URL with the same names the API uses, so reloading or sharing keeps them. */
export interface IncidentFilters {
  criticality: Criticality[];
  category: IncidentCategory[];
}

export interface QueueFilters extends IncidentFilters {
  assignedToMe: boolean;
}

export function parseIncidentFilters(params: URLSearchParams): IncidentFilters {
  return {
    criticality: pick(params.getAll("criticality"), CRITICALITIES),
    category: pick(params.getAll("category"), CATEGORIES),
  };
}

export function incidentSearchParams(filters: IncidentFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const value of filters.criticality) params.append("criticality", value);
  for (const value of filters.category) params.append("category", value);
  return params;
}

export function parseQueueFilters(params: URLSearchParams): QueueFilters {
  // Any value other than "true" turns the filter off, so a hand-edited URL never breaks the queue.
  return { ...parseIncidentFilters(params), assignedToMe: params.get("assigned_to_me") === "true" };
}

export function queueSearchParams(filters: QueueFilters): URLSearchParams {
  const params = incidentSearchParams(filters);
  if (filters.assignedToMe) params.set("assigned_to_me", "true");
  return params;
}

export function toggle<T>(values: readonly T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export function hasIncidentFilters(filters: IncidentFilters): boolean {
  return filters.criticality.length > 0 || filters.category.length > 0;
}

export function hasFilters(filters: QueueFilters): boolean {
  return hasIncidentFilters(filters) || filters.assignedToMe;
}

// A hand-edited URL never reaches the API with a value it would reject.
export function pick<T extends string>(values: string[], allowed: readonly T[]): T[] {
  return allowed.filter((value) => values.includes(value));
}
