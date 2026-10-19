import { describe, expect, it } from "vitest";

import { openDialog } from "./dialog-lifecycle";

function fakeDialog() {
  const calls: string[] = [];
  const dialog = {
    open: false,
    showModal() {
      calls.push("showModal");
      dialog.open = true;
    },
    close() {
      calls.push("close");
      dialog.open = false;
    },
  };
  return { dialog, calls };
}

describe("openDialog", () => {
  it("opens the dialog as a modal", () => {
    const { dialog, calls } = fakeDialog();

    openDialog(dialog);

    expect(calls).toEqual(["showModal"]);
  });

  it("closes it in the cleanup, so the browser gives focus back to what opened it", () => {
    // Removing an open <dialog> from the page skips close(), and focus falls to the body.
    const { dialog, calls } = fakeDialog();

    const cleanup = openDialog(dialog);
    cleanup();

    expect(calls).toEqual(["showModal", "close"]);
  });

  it("does not open twice", () => {
    const { dialog, calls } = fakeDialog();
    dialog.open = true;

    openDialog(dialog);

    expect(calls).toEqual([]);
  });
});
