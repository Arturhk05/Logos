import { useQuery } from "@tanstack/react-query";

import { useNow } from "../../shared/useNow";
import { myReportsQueryOptions } from "./api";
import { MyReportsView } from "./MyReportsView";

export function MyReportsPage() {
  const query = useQuery(myReportsQueryOptions);
  const now = useNow(60_000);

  return (
    <MyReportsView
      state={query.isPending ? "loading" : query.data === undefined ? "error" : "ready"}
      errorMessage={query.error?.message}
      onRetry={() => {
        void query.refetch();
      }}
      items={query.data ?? []}
      now={now}
    />
  );
}
