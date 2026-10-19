import { CircleAlert, CircleCheck, Lock, RotateCw, Send } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import { CRITICALITIES, CRITICALITY_LABELS, type Criticality } from "../../shared/labels";
import { phoneEnding } from "../../shared/phone";
import { Button } from "../../shared/ui/Button";
import { CategoryIcon } from "../../shared/ui/CategoryIcon";
import { TableSkeleton } from "../../shared/ui/Skeleton";
import { ErrorState } from "../../shared/ui/StateMessage";
import type { CategoryOption, ReportDraft, ReportErrors } from "./report";

export interface ReportViewProps {
  categoriesState: "loading" | "error" | "ready";
  categoriesError?: string;
  onRetryCategories: () => void;
  options: CategoryOption[];
  draft: ReportDraft;
  errors: ReportErrors;
  onCategory: (option: CategoryOption) => void;
  onCriticality: (criticality: Criticality) => void;
  onField: (field: "location" | "description", value: string) => void;
  onSubmit: () => void;
  pending: boolean;
  submitError?: string;
  created?: { id: number; phone: string };
  onReportAnother: () => void;
}

const LOCATION_MAX_LENGTH = 200;
const DESCRIPTION_MAX_LENGTH = 1000;

const INPUT =
  "w-full rounded-xl border border-line bg-surface px-3 text-base text-ink placeholder:text-muted focus:border-accent focus:outline-none";

// Every choice is at least 44 px tall (RNF-07), on a phone held with one hand.
const CHOICE =
  "flex min-h-11 items-center gap-2 rounded-xl border px-3 text-left transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40";

function choiceLook(pressed: boolean, critical = false): string {
  if (!pressed) return "border-line bg-surface hover:border-line-strong";
  return critical
    ? "border-critical bg-critical font-semibold text-on-critical"
    : "border-accent bg-accent font-semibold text-on-accent";
}

export function ReportView(props: ReportViewProps) {
  if (props.created !== undefined) {
    return <Created {...props.created} onReportAnother={props.onReportAnother} />;
  }

  const { draft, errors } = props;
  const chosen = props.options.find((option) => option.category === draft.category);
  const locked = chosen?.criticality_locked === true;

  return (
    <form
      noValidate
      className="flex flex-col gap-5"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <h1 className="text-xl font-bold tracking-tight">Reportar incidente</h1>

      <fieldset className="flex flex-col gap-2">
        <legend className="mb-2 text-sm font-semibold">Categoria</legend>
        {props.categoriesState === "loading" && <TableSkeleton rows={3} />}
        {props.categoriesState === "error" && (
          <ErrorState message={props.categoriesError ?? ""} onRetry={props.onRetryCategories} />
        )}
        {props.categoriesState === "ready" && (
          // Every row as tall as the tallest, so all buttons match; one column on very narrow phones,
          // where the longest name would otherwise wrap into four lines.
          <div className="grid auto-rows-fr grid-cols-1 gap-2 min-[360px]:grid-cols-2">
            {props.options.map((option) => (
              <button
                key={option.category}
                type="button"
                aria-pressed={draft.category === option.category}
                className={`${CHOICE} text-[13px] leading-snug ${choiceLook(draft.category === option.category)}`}
                onClick={() => {
                  props.onCategory(option);
                }}
              >
                <CategoryIcon category={option.category} className="size-5 shrink-0" />
                {option.label}
              </button>
            ))}
          </div>
        )}
        <FieldError message={errors.category} />
      </fieldset>

      <fieldset className="flex flex-col gap-2">
        <legend className="mb-2 text-sm font-semibold">Criticidade</legend>
        <div className="grid grid-cols-3 gap-2">
          {CRITICALITIES.map((criticality) => (
            <button
              key={criticality}
              type="button"
              aria-pressed={draft.criticality === criticality}
              disabled={draft.category === null || (locked && criticality !== "HIGH")}
              className={`${CHOICE} justify-center text-sm ${choiceLook(
                draft.criticality === criticality,
                criticality === "HIGH",
              )}`}
              onClick={() => {
                props.onCriticality(criticality);
              }}
            >
              {CRITICALITY_LABELS[criticality]}
            </button>
          ))}
        </div>
        <p className="flex min-h-5 items-center gap-1.5 text-sm leading-5 text-muted">
          {locked ? (
            <>
              <Lock aria-hidden className="size-4" />
              Sempre Alta para acidente com vítimas
            </>
          ) : draft.category === null ? (
            "Sugerida conforme a categoria escolhida."
          ) : (
            "Sugerida conforme a categoria; você pode alterar."
          )}
        </p>
      </fieldset>

      <Field label="Local" error={errors.location}>
        <input
          className={`${INPUT} min-h-12`}
          name="location"
          maxLength={LOCATION_MAX_LENGTH}
          placeholder="Ex.: BR-116, km 230"
          value={draft.location}
          aria-invalid={errors.location !== undefined}
          onChange={(event) => {
            props.onField("location", event.target.value);
          }}
        />
      </Field>

      <Field label="Descrição" error={errors.description}>
        <textarea
          className={`${INPUT} min-h-28 py-3`}
          name="description"
          maxLength={DESCRIPTION_MAX_LENGTH}
          placeholder="O que aconteceu?"
          value={draft.description}
          aria-invalid={errors.description !== undefined}
          onChange={(event) => {
            props.onField("description", event.target.value);
          }}
        />
      </Field>

      <div className="flex flex-col gap-2">
        <FieldError message={props.submitError} />
        <Button type="submit" pending={props.pending} className="min-h-12 text-base">
          {props.submitError === undefined ? (
            <>
              <Send aria-hidden className="size-4" />
              Enviar reporte
            </>
          ) : (
            <>
              <RotateCw aria-hidden className="size-4" />
              Tentar novamente
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex flex-col gap-2 text-sm font-semibold">
        {label}
        {children}
      </label>
      <FieldError message={error} />
    </div>
  );
}

/** Always rendered with room for one line, so a message never pushes the form down. */
function FieldError({ message }: { message?: string }) {
  return (
    <p
      role="alert"
      className="flex min-h-5 items-start gap-1.5 text-sm leading-5 text-critical-ink"
    >
      {message !== undefined && (
        <>
          <CircleAlert aria-hidden className="mt-0.5 size-4 shrink-0" />
          {message}
        </>
      )}
    </p>
  );
}

function Created({
  id,
  phone,
  onReportAnother,
}: {
  id: number;
  phone: string;
  onReportAnother: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 py-10 text-center">
      <CircleCheck aria-hidden className="size-12 text-ink" />
      <div>
        <p className="text-lg font-bold">Incidente #{id} enviado.</p>
        <p className="text-muted">
          A central já foi avisada e vai entrar em contato pelo WhatsApp no número terminado em{" "}
          {phoneEnding(phone)}.
        </p>
      </div>
      <div className="flex w-full flex-col gap-2">
        <Link
          to="/meus-reportes"
          className="flex min-h-12 items-center justify-center rounded-lg bg-accent px-4 font-semibold text-on-accent"
        >
          Ver meus reportes
        </Link>
        <Button variant="secondary" className="min-h-12" onClick={onReportAnother}>
          Reportar outro
        </Button>
      </div>
    </div>
  );
}
