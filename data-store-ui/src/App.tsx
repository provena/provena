import { ReactKeycloakProvider } from "@react-keycloak/web";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { observer } from "mobx-react-lite";
import { keycloak } from "react-libs";
import RoutesAndLayout from "./layout/RoutesAndLayout";
import { WarningBanner } from "react-libs/components/WarningBanner";

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
      <QueryClientProvider client={queryClient}>
        <ReactKeycloakProvider authClient={keycloak}>
          <WarningBanner
            title="System Degradation - Do Not Register New Items"
            message="The RRAP M&DS Information System is experiencing degraded performance due to PID minting service issues. Please DO NOT register new items or lodge new provenance records until normal function is restored. We have notified the service provider and will update you when resolved. Contact the RRAP M&DS IS team if you have concerns."
            severity="error"
            showIcon={true}
            dismissible={false}
            children={<RoutesAndLayout />}
          />
        </ReactKeycloakProvider>
      </QueryClientProvider>
    </div>
  );
}

export default observer(App);
