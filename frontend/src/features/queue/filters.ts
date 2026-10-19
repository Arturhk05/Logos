import {
  CATEGORIES,
  CRITICALITIES,
  type Criticality,
  type IncidentCategory,
} from "../../shared/labels";

/** Queue filters, kept in the URL with the same names the API uses, so reloading or sharing keeps them. */
export interface QueueFilters {
  criticality: Criticality[];
  category: IncidentCategory[];
}

export function parseQueueFilters(params: URLSearchParams): QueueFilters {
  return {
    criticality: pick(params.getAll("criticality"), CRITICALITIES),
    category: pick(params.getAll("category"), CATEGORIES),
  };
}

export function queueSearchParams(filters: QueueFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const value of filters.criticality) params.append("criticality", value);
  for (const value of filters.category) params.append("category", value);
  return params;
}

export function toggle<T>(values: readonly T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

export function hasFilters(filters: QueueFilters): boolean {
  return filters.criticality.length > 0 || filters.category.length > 0;
}

// A hand-edited URL never reaches the API with a value it would reject.
export function pick<T extends string>(values: string[], allowed: readonly T[]): T[] {
  return allowed.filter((value) => values.includes(value));
}
