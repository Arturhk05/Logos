import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { categoriesQueryOptions, myReportsQueryOptions, reportIncident } from "./api";
import {
  EMPTY_DRAFT,
  selectCategory,
  toReportRequest,
  validateReport,
  type ReportErrors,
  type ReportIncidentRequest,
} from "./report";
import { ReportView } from "./ReportView";

export function ReportPage() {
  const queryClient = useQueryClient();
  const categories = useQuery(categoriesQueryOptions);
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [errors, setErrors] = useState<ReportErrors>({});
  // One key per report: every attempt of this draft reuses it, so the API creates it only once.
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());
  const [created, setCreated] = useState<{ id: number }>();

  const mutation = useMutation({
    mutationFn: ({ body, key }: { body: ReportIncidentRequest; key: string }) =>
      reportIncident(body, key),
    onSuccess: (incident) => {
      setCreated({ id: incident.id });
      setDraft(EMPTY_DRAFT);
      setIdempotencyKey(crypto.randomUUID());
      void queryClient.invalidateQueries({ queryKey: myReportsQueryOptions.queryKey });
    },
  });

  return (
    <ReportView
      categoriesState={
        categories.isPending ? "loading" : categories.data === undefined ? "error" : "ready"
      }
      categoriesError={categories.error?.message}
      onRetryCategories={() => {
        void categories.refetch();
      }}
      options={categories.data ?? []}
      draft={draft}
      errors={errors}
      onCategory={(option) => {
        setDraft((current) => selectCategory(current, option));
        setErrors((current) => ({ ...current, category: undefined }));
      }}
      onCriticality={(criticality) => {
        setDraft((current) => ({ ...current, criticality }));
      }}
      onField={(field, value) => {
        setDraft((current) => ({ ...current, [field]: value }));
        setErrors((current) => ({ ...current, [field]: undefined }));
      }}
      onSubmit={() => {
        const found = validateReport(draft);
        setErrors(found);
        if (Object.keys(found).length > 0) return;
        mutation.mutate({ body: toReportRequest(draft), key: idempotencyKey });
      }}
      pending={mutation.isPending}
      submitError={mutation.error?.message}
      created={created}
      onReportAnother={() => {
        setCreated(undefined);
        mutation.reset();
      }}
    />
  );
}
