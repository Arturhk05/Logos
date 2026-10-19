import { X } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, type ReactNode } from "react";

import { openDialog } from "./dialog-lifecycle";

const VARIANTS = {
  // Full screen on phones; a panel on the right from md up.
  drawer:
    "m-0 ml-auto h-dvh max-h-dvh w-full max-w-none md:max-w-xl md:border-l md:border-line md:shadow-2xl",
  modal: "m-auto w-[calc(100%-2rem)] max-w-md rounded-xl shadow-2xl",
};

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  variant?: keyof typeof VARIANTS;
  children: ReactNode;
}

/** Native <dialog>: focus trapping and Esc come from the browser. */
export function Dialog({ open, onClose, title, variant = "modal", children }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);

  // A layout effect, so the cleanup closes the dialog before React removes it from the page.
  useLayoutEffect(() => {
    const dialog = ref.current;
    if (dialog === null || !open) return;
    return openDialog(dialog);
  }, [open]);

  useEffect(() => {
    const dialog = ref.current;
    if (dialog === null) return;
    // Esc fires "cancel"; the state stays the source of truth, so the dialog only closes through onClose.
    const cancel = (event: Event) => {
      event.preventDefault();
      onClose();
    };
    // A click on the dialog itself, not on its content, is a click on the backdrop.
    const clickOutside = (event: MouseEvent) => {
      if (event.target === dialog) onClose();
    };
    dialog.addEventListener("cancel", cancel);
    dialog.addEventListener("click", clickOutside);
    return () => {
      dialog.removeEventListener("cancel", cancel);
      dialog.removeEventListener("click", clickOutside);
    };
  }, [onClose]);

  return (
    <dialog
      ref={ref}
      aria-label={title}
      className={`bg-surface p-0 text-ink backdrop:bg-zinc-900/30 ${VARIANTS[variant]}`}
    >
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-3">
          <h2 className="text-base font-semibold">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar"
            className="inline-flex size-10 items-center justify-center rounded-lg text-muted hover:bg-canvas hover:text-ink"
          >
            <X aria-hidden className="size-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </dialog>
  );
}
