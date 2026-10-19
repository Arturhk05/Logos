type DialogElement = Pick<HTMLDialogElement, "open" | "showModal" | "close">;

/**
 * Shows the dialog as a modal and returns the cleanup that closes it. Closing explicitly matters:
 * a <dialog> removed from the page while open skips close(), and focus falls to the body instead of
 * going back to the element that opened it.
 */
export function openDialog(dialog: DialogElement): () => void {
  if (!dialog.open) dialog.showModal();
  return () => {
    if (dialog.open) dialog.close();
  };
}
