import { CircleAlert } from "lucide-react";
import { Link } from "react-router";

/** Replaces React Router's default error page, which is in English and shows the stack trace. */
export function AppError() {
  return (
    <main
      role="alert"
      className="flex min-h-dvh flex-col items-center justify-center gap-4 px-4 text-center"
    >
      <CircleAlert aria-hidden className="size-10 text-muted" />
      <p className="text-lg font-semibold">Ocorreu um erro inesperado.</p>
      <p className="max-w-sm text-muted">Volte ao início e tente de novo.</p>
      <Link
        to="/"
        className="flex min-h-11 items-center rounded-lg bg-accent px-4 font-semibold text-on-accent"
      >
        Voltar ao início
      </Link>
    </main>
  );
}
