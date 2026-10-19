import type { components } from "../api/schema";

export type Criticality = components["schemas"]["Criticality"];
export type IncidentStatus = components["schemas"]["IncidentStatus"];
export type IncidentCategory = components["schemas"]["IncidentCategory"];
export type UserRole = components["schemas"]["UserRole"];

// Most critical first, the order of the queue (RN-01).
export const CRITICALITIES: readonly Criticality[] = ["HIGH", "MEDIUM", "LOW"];

export const CATEGORIES: readonly IncidentCategory[] = [
  "VEHICLE_ACCIDENT",
  "ACCIDENT_WITH_VICTIMS",
  "ADVERSE_WEATHER",
  "MECHANICAL_PROBLEM",
  "ROAD_BLOCKAGE",
];

// Same names as the API's labels, so a screen and an API message never disagree.
export const CRITICALITY_LABELS: Record<Criticality, string> = {
  HIGH: "Alta",
  MEDIUM: "Média",
  LOW: "Baixa",
};

export const STATUS_LABELS: Record<IncidentStatus, string> = {
  OPEN: "Aberto",
  INVESTIGATING: "Em Investigação",
  CLOSED: "Fechado",
  INCONCLUSIVE: "Inconclusivo",
};

export const CATEGORY_LABELS: Record<IncidentCategory, string> = {
  VEHICLE_ACCIDENT: "Acidente com Veículo",
  ACCIDENT_WITH_VICTIMS: "Acidente com Vítimas",
  ADVERSE_WEATHER: "Condição Climática Atípica na Pista",
  MECHANICAL_PROBLEM: "Problema Mecânico",
  ROAD_BLOCKAGE: "Bloqueio de Pista",
};

export const ROLE_LABELS: Record<UserRole, string> = {
  ANALYST: "Analista",
  SUPERVISOR: "Supervisor",
  DRIVER: "Motorista",
};
