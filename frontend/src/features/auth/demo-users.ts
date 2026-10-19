import type { UserRole } from "../../shared/labels";

// Created by the backend seed (backend/README.md); the brief asks for the credentials on the first screen.
export const DEMO_PASSWORD = "logos123";

export const DEMO_USERS: readonly { username: string; role: UserRole }[] = [
  { username: "camila", role: "ANALYST" },
  { username: "lucas", role: "ANALYST" },
  { username: "roberto", role: "SUPERVISOR" },
  { username: "jose", role: "DRIVER" },
];
