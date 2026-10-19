import { describe, expect, it } from "vitest";

import { CATEGORY_LABELS, CRITICALITY_LABELS, ROLE_LABELS, STATUS_LABELS } from "./labels";

describe("labels", () => {
  it("labels every criticality, status, category and role in Portuguese", () => {
    expect(CRITICALITY_LABELS).toEqual({ HIGH: "Alta", MEDIUM: "Média", LOW: "Baixa" });
    expect(STATUS_LABELS).toEqual({
      OPEN: "Aberto",
      INVESTIGATING: "Em Investigação",
      CLOSED: "Fechado",
      INCONCLUSIVE: "Inconclusivo",
    });
    expect(CATEGORY_LABELS).toEqual({
      VEHICLE_ACCIDENT: "Acidente com Veículo",
      ACCIDENT_WITH_VICTIMS: "Acidente com Vítimas",
      ADVERSE_WEATHER: "Condição Climática Atípica na Pista",
      MECHANICAL_PROBLEM: "Problema Mecânico",
      ROAD_BLOCKAGE: "Bloqueio de Pista",
    });
    expect(ROLE_LABELS).toEqual({
      ANALYST: "Analista",
      SUPERVISOR: "Supervisor",
      DRIVER: "Motorista",
    });
  });
});
