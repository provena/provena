import {
  captureConsoleIntegration,
  extraErrorDataIntegration,
} from "@sentry/integrations";
import * as Sentry from "@sentry/react";

// Sentry init configs
export interface SentryInitProps {
  currentUI?: string;
  // Sentry debug mode, default to false
  debug?: boolean;
}
export const sentryInit = (props: SentryInitProps) => {
  // Configuration should happen as early as possible in application's lifecycle.
  // Config refer to https://docs.sentry.io/platforms/javascript/guides/react/configuration/

  const sentryDSN = import.meta.env.VITE_SENTRY_DSN;
  const envStage = import.meta.env.VITE_STAGE;
  const featureNo = import.meta.env.VITE_FEATURE_NUMBER;
  const releaseVer = import.meta.env.VITE_GIT_COMMIT_ID;
  // disable only if VITE_MONITORING_ENABLED string is empty or undefined
  const enableMonitor = !!import.meta.env.VITE_MONITORING_ENABLED;
  // if feature number exsits and not empty, Sentry environment value will be: VITE_STAGE:VITE_FEATURE_NUMBER
  // otherwise, Sentry environment value will only be: VITE_STAGE
  const sentryEnv = !!featureNo ? envStage + ":" + featureNo : envStage;

  Sentry.init({
    dsn: sentryDSN,
    enabled: enableMonitor,
    debug: props.debug ?? false,
    release: releaseVer,
    environment: sentryEnv,

    integrations: [
      // captures transactions, route location from the browser
      Sentry.browserTracingIntegration(),
      Sentry.breadcrumbsIntegration({
        // Console logs are all generated from instrument.js file,
        // solve this problem by turnning this off in breadcrumb integration:
        // https://github.com/getsentry/sentry-react-native/issues/794
        console: false,
      }),
      //capture uncaught exceptions and unhandled rejections.
      Sentry.globalHandlersIntegration({
        onerror: true,
        // https://docs.sentry.io/platforms/javascript/guides/react/usage/
        onunhandledrejection: true,
      }),

      // Captures all Console calls via `captureException` or `captureMessage`.
      // include messages from console.error(), console.assert()
      captureConsoleIntegration({ levels: ["error", "assert"] }),
      // adds non-native attributes from the error object to the event as extra data.
      extraErrorDataIntegration({ depth: 10 }),
    ],

    enableTracing: true,
    autoSessionTracking: true,
    // total amount of breadcrumbs that should be captured
    maxBreadcrumbs: 30,
    sampleRate: 1.0,
    tracesSampleRate: 1.0,
    // A list of regex patterns that match error messages that shouldn't be sent to Sentry
    // exclude "Warning:" error messages
    ignoreErrors: [/Warning:/],
    // limit how deep the object serializer should go,
    // any data beyond normalizeDepth will be trimmed and marked using its type instead ([Object] or [Array])
    normalizeDepth: 10,
  });

  Sentry.setTag("UI", props.currentUI);
};
