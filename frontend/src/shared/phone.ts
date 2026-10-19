import type { IncidentDetail } from "../api/client";
import { CATEGORY_LABELS } from "./labels";

/** Phones come from the API as digits with the country code, the format WhatsApp links expect. */
const BRAZILIAN_PHONE = /^55(\d{2})(\d{4,5})(\d{4})$/;

/** "5500900000001" as "(00) 90000-0001"; any other format is shown as it came. */
export function formatPhone(phone: string): string {
  const match = BRAZILIAN_PHONE.exec(phone);
  if (match === null) return phone;
  const [, area, prefix, line] = match;
  return `(${area ?? ""}) ${prefix ?? ""}-${line ?? ""}`;
}

export function phoneEnding(phone: string): string {
  return phone.slice(-4);
}

export function whatsAppLink(phone: string, message: string): string {
  return `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
}

export function incidentContactMessage(
  incident: Pick<IncidentDetail, "id" | "category" | "location">,
): string {
  return `Olá! Aqui é a central Logos, sobre o incidente #${String(incident.id)} (${CATEGORY_LABELS[incident.category]}, ${incident.location}).`;
}
