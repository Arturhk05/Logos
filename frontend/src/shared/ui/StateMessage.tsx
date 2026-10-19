import { CircleAlert, Inbox, RotateCw } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "./Button";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 px-4 py-12 text-center">
      <CircleAlert aria-hidden className="size-8 text-muted" />
      <p className="max-w-sm">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry} className="min-h-11">
          <RotateCw aria-hidden className="size-4" />
          Tentar novamente
        </Button>
      )}
    </div>
  );
}

export function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 px-4 py-12 text-center">
      <Inbox aria-hidden className="size-8 text-muted" />
      <p className="max-w-sm text-muted">{message}</p>
      {action}
    </div>
  );
}
