import { createBrowserRouter } from "react-router";

import { LoginPage } from "../features/auth/LoginPage";
import { MyReportsPage } from "../features/driver/MyReportsPage";
import { ReportPage } from "../features/driver/ReportPage";
import { HistoryPage } from "../features/history/HistoryPage";
import { QueuePage } from "../features/queue/QueuePage";
import { CentralLayout } from "./CentralLayout";
import { DriverLayout } from "./DriverLayout";
import { HomeRedirect, RequireRole } from "./RequireRole";
import { SessionGate } from "./SessionGate";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <SessionGate />,
    children: [
      {
        element: <RequireRole area="central" />,
        children: [
          {
            element: <CentralLayout />,
            children: [
              { path: "/fila/:incidentId?", element: <QueuePage /> },
              { path: "/historico/:incidentId?", element: <HistoryPage /> },
            ],
          },
        ],
      },
      {
        element: <RequireRole area="driver" />,
        children: [
          {
            element: <DriverLayout />,
            children: [
              { path: "/reportar", element: <ReportPage /> },
              { path: "/meus-reportes", element: <MyReportsPage /> },
            ],
          },
        ],
      },
      // "/" and unknown paths go to the user's home.
      { path: "*", element: <HomeRedirect /> },
    ],
  },
]);
