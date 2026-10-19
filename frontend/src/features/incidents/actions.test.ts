import { describe, expect, it } from "vitest";

import {
  ACTION_TARGET,
  availableActions,
  needsConfirmation,
  needsReason,
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
