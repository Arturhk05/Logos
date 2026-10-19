import { describe, expect, it } from "vitest";

import {
  ACTION_TARGET,
  acceptsReason,
  availableActions,
  confirmationState,
  needsConfirmation,
  needsReason,
  reasonToSend,
  type IncidentAction,
} from "./actions";

const camila = { id: 1, username: "camila" };
const lucas = { id: 2, username: "lucas" };

// Written by hand from RN-02 (assume), RN-03 (who may change) and RN-04 (allowed transitions).
describe("availableActions", () => {
  it.each([
    ["OPEN", null, "ANALYST", ["assume"]],
    ["OPEN", null, "SUPERVISOR", ["assume"]],
    ["OPEN", null, "DRIVER", []],
    ["INVESTIGATING", camila, "ANALYST", ["close", "inconclusive", "reopen"]],
    ["INVESTIGATING", lucas, "ANALYST", []],
    ["INVESTIGATING", lucas, "SUPERVISOR", ["close", "inconclusive", "reopen"]],
    ["CLOSED", lucas, "SUPERVISOR", []],
    ["INCONCLUSIVE", lucas, "SUPERVISOR", []],
  ] as const)(
    "%s assigned to %o, seen by camila as %s, allows %o",
    (status, assignee, role, expected) => {
      expect(availableActions({ status, assignee }, { id: 1, role })).toEqual(expected);
    },
  );
});

describe("needsReason", () => {
  it("asks for a reason only when closing", () => {
    const actions: IncidentAction[] = ["close", "inconclusive", "reopen", "assume"];

    expect(actions.map(needsReason)).toEqual([true, true, false, false]);
  });
});

describe("acceptsReason", () => {
  it("takes a reason when closing, and an optional one when sending back to the queue", () => {
    const actions: IncidentAction[] = ["close", "inconclusive", "reopen", "assume"];

    expect(actions.map(acceptsReason)).toEqual([true, true, true, false]);
  });
});

describe("reasonToSend", () => {
  it.each([
    ["reopen", "", undefined],
    ["reopen", "   ", undefined],
    ["reopen", " Saiu do turno ", "Saiu do turno"],
    ["close", " Pista liberada ", "Pista liberada"],
    ["inconclusive", "Sem contato", "Sem contato"],
  ] as const)("%s with %o sends %o", (action, reason, expected) => {
    expect(reasonToSend(action, reason)).toBe(expected);
  });
});

describe("needsConfirmation", () => {
  it("confirms every status change, but assuming happens on one click", () => {
    const actions: IncidentAction[] = ["close", "inconclusive", "reopen", "assume"];

    expect(actions.map(needsConfirmation)).toEqual([true, true, true, false]);
  });
});

describe("ACTION_TARGET", () => {
  it("maps each status action to its target status", () => {
    expect(ACTION_TARGET).toEqual({
      close: "CLOSED",
      inconclusive: "INCONCLUSIVE",
      reopen: "OPEN",
    });
  });
});

describe("confirmationState", () => {
  const supervisor = { id: 3, role: "SUPERVISOR" } as const;
  const investigating = { status: "INVESTIGATING", assignee: lucas } as const;

  it("lets the user confirm a close with a reason", () => {
    expect(confirmationState("close", investigating, supervisor, "Pista liberada")).toEqual({
      unavailable: false,
      canConfirm: true,
    });
  });

  it("waits for a reason that is not only spaces", () => {
    expect(confirmationState("close", investigating, supervisor, "   ")).toEqual({
      unavailable: false,
      canConfirm: false,
    });
  });

  it("needs no reason to send back to the queue", () => {
    expect(confirmationState("reopen", investigating, supervisor, "")).toEqual({
      unavailable: false,
      canConfirm: true,
    });
  });

  it("blocks the action once the incident no longer allows it", () => {
    const closed = { status: "CLOSED", assignee: lucas } as const;

    expect(confirmationState("close", closed, supervisor, "Pista liberada")).toEqual({
      unavailable: true,
      canConfirm: false,
    });
  });

  it("blocks the action while the incident is unknown", () => {
    expect(confirmationState("reopen", undefined, supervisor, "")).toEqual({
      unavailable: true,
      canConfirm: false,
    });
  });
});
