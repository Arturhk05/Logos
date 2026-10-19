import { describe, expect, it } from "vitest";

import {
  EMPTY_DRAFT,
  selectCategory,
  toReportRequest,
  validateReport,
  type CategoryOption,
  type ReportDraft,
} from "./report";

const victims: CategoryOption = {
  category: "ACCIDENT_WITH_VICTIMS",
  label: "Acidente com Vítimas",
  suggested_criticality: "HIGH",
  criticality_locked: true,
};

const blockage: CategoryOption = {
  category: "ROAD_BLOCKAGE",
  label: "Bloqueio de Pista",
  suggested_criticality: "MEDIUM",
  criticality_locked: false,
};

describe("selectCategory", () => {
  it("suggests the criticality of the chosen category", () => {
    expect(selectCategory({ ...EMPTY_DRAFT, criticality: "LOW" }, blockage)).toMatchObject({
      category: "ROAD_BLOCKAGE",
      criticality: "MEDIUM",
    });
  });

  it("sets high criticality for accidents with victims", () => {
    expect(selectCategory(EMPTY_DRAFT, victims)).toMatchObject({ criticality: "HIGH" });
  });

  it("keeps what was typed", () => {
    const draft = { ...EMPTY_DRAFT, location: "BR-101, km 45", description: "Carreta tombada" };

    expect(selectCategory(draft, blockage)).toMatchObject({
      location: "BR-101, km 45",
      description: "Carreta tombada",
    });
  });
});

describe("validateReport", () => {
  it("names each missing field", () => {
    expect(validateReport({ ...EMPTY_DRAFT, location: "   " })).toEqual({
      category: "Escolha a categoria.",
      location: "Informe o local.",
      description: "Descreva o que aconteceu.",
    });
  });

  it("accepts a complete draft", () => {
    const draft: ReportDraft = {
      category: "ROAD_BLOCKAGE",
      criticality: "MEDIUM",
      location: "BR-101, km 45",
      description: "Carreta tombada",
    };

    expect(validateReport(draft)).toEqual({});
  });
});

describe("toReportRequest", () => {
  it("trims the text and keeps the chosen criticality", () => {
    const draft: ReportDraft = {
      category: "ROAD_BLOCKAGE",
      criticality: "LOW",
      location: " BR-101, km 45 ",
      description: " Carreta tombada ",
    };

    expect(toReportRequest(draft)).toEqual({
      category: "ROAD_BLOCKAGE",
      criticality: "LOW",
      location: "BR-101, km 45",
      description: "Carreta tombada",
    });
  });
});
