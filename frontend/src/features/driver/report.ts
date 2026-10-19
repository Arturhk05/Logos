import type { components } from "../../api/schema";
import type { Criticality, IncidentCategory } from "../../shared/labels";

export type CategoryOption = components["schemas"]["CategoryOptionResponse"];
export type ReportIncidentRequest = components["schemas"]["ReportIncidentRequest"];

export interface ReportDraft {
  category: IncidentCategory | null;
  criticality: Criticality | null;
  location: string;
  description: string;
}

export type ReportField = "category" | "location" | "description";
export type ReportErrors = Partial<Record<ReportField, string>>;

export const EMPTY_DRAFT: ReportDraft = {
  category: null,
  criticality: null,
  location: "",
  description: "",
};

/** Picking a category fills in its suggested criticality (RN-10); the driver may still change it. */
export function selectCategory(draft: ReportDraft, option: CategoryOption): ReportDraft {
  return { ...draft, category: option.category, criticality: option.suggested_criticality };
}

export function validateReport(draft: ReportDraft): ReportErrors {
  const errors: ReportErrors = {};
  if (draft.category === null) errors.category = "Escolha a categoria.";
  if (draft.location.trim() === "") errors.location = "Informe o local.";
  if (draft.description.trim() === "") errors.description = "Descreva o que aconteceu.";
  return errors;
}

/** Only called on a draft that passed validateReport. */
export function toReportRequest(draft: ReportDraft): ReportIncidentRequest {
  if (draft.category === null) throw new Error("toReportRequest needs a category");
  return {
    category: draft.category,
    criticality: draft.criticality,
    location: draft.location.trim(),
    description: draft.description.trim(),
  };
}
