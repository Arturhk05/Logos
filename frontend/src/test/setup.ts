import { afterAll, afterEach, beforeAll, vi } from "vitest";

import { server } from "./server";

// The client reads the page origin at import time, so this stays stubbed for the whole file.
vi.stubGlobal("location", new URL("http://localhost"));

let unhandledRequests = 0;

beforeAll(() => {
  server.listen({
    onUnhandledFrame({ defaults }) {
      unhandledRequests += 1;
      defaults.error();
    },
  });
});
afterEach(() => {
  server.resetHandlers();
  const count = unhandledRequests;
  unhandledRequests = 0;
  // The client turns MSW's rejection into a network error, so the test itself could still pass.
  if (count > 0)
    throw new Error(`${String(count)} request(s) had no handler; see the error above.`);
});
afterAll(() => {
  server.close();
});
