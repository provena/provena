import { ReactKeycloakProvider } from "@react-keycloak/web";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { observer } from "mobx-react-lite";
import RoutesAndLayout from "./layout/RoutesAndLayout";
import { keycloak } from "react-libs";
import { AdapterMoment } from "@mui/x-date-pickers/AdapterMoment";
import { LocalizationProvider } from "@mui/x-date-pickers";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

function App() {
  return (
    <div>
      <LocalizationProvider dateAdapter={AdapterMoment}>
        <QueryClientProvider client={queryClient}>
          <ReactKeycloakProvider authClient={keycloak}>
            <RoutesAndLayout />
          </ReactKeycloakProvider>
        </QueryClientProvider>
      </LocalizationProvider>
    </div>
  );
}

export default observer(App);
