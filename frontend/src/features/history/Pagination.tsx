import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "../../shared/ui/Button";

interface PaginationProps {
  page: number;
  pageCount: number;
  onPage: (page: number) => void;
}

export function Pagination({ page, pageCount, onPage }: PaginationProps) {
  return (
    <nav aria-label="Páginas" className="flex items-center justify-end gap-2 text-sm">
      <Button
        variant="secondary"
        disabled={page <= 1}
        onClick={() => {
          onPage(page - 1);
        }}
      >
        <ChevronLeft aria-hidden className="size-4" />
        Anterior
      </Button>
      <span className="min-w-28 text-center text-muted tabular-nums" aria-live="polite">
        Página {page} de {pageCount}
      </span>
      <Button
        variant="secondary"
        disabled={page >= pageCount}
        onClick={() => {
          onPage(page + 1);
        }}
      >
        Próxima
        <ChevronRight aria-hidden className="size-4" />
      </Button>
    </nav>
  );
}
