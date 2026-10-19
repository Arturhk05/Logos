import {
  Ambulance,
  Car,
  CloudLightning,
  Construction,
  Wrench,
  type LucideIcon,
} from "lucide-react";

import type { IncidentCategory } from "../labels";

const ICONS: Record<IncidentCategory, LucideIcon> = {
  VEHICLE_ACCIDENT: Car,
  ACCIDENT_WITH_VICTIMS: Ambulance,
  ADVERSE_WEATHER: CloudLightning,
  MECHANICAL_PROBLEM: Wrench,
  ROAD_BLOCKAGE: Construction,
};

// Decorative: the category name is always written next to it.
export function CategoryIcon({
  category,
  className = "size-4",
}: {
  category: IncidentCategory;
  className?: string;
}) {
  const Icon = ICONS[category];
  return <Icon aria-hidden className={className} />;
}
