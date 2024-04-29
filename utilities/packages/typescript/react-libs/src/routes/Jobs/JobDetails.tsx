import { Stack } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import {
  BATCH_ID_QSTRING,
  JobNavigationComponent,
  useJobMonitor,
  useQString,
} from "../../";
import { JobStatusTable } from "../../provena-interfaces/AsyncJobAPI";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      backgroundColor: theme.palette.common.white,
      padding: theme.spacing(3),
      borderRadius: 5,
    },
  }),
);

export interface SingleJobDetailsComponentProps {
  sessionId: string;
  showIO: boolean;
  refetchOnError: boolean;
  onJobSuccess?: (entry: JobStatusTable) => void;
  adminMode: boolean;
}
export const SingleJobDetailsComponent = (
  props: SingleJobDetailsComponentProps,
) => {
  /**
    Component: SingleJobDetailsComponent

    Renders and monitors the details for a job
    
    */
  const monitor = useJobMonitor({
    showIO: props.showIO,
    sessionId: props.sessionId,
    refetchOnError: props.refetchOnError,
    onJobSuccess: props.onJobSuccess,
    adminMode: props.adminMode,
  });

  return monitor.render();
};

export const JOB_DETAILS_ROUTE = "/jobs/details";
export const SESSION_ID_QSTRING = "sessionId";
export const DETAIL_ADMIN_MODE_QSTRING = "adminMode";

export interface JobDetailsComponentProps {}
export const JobDetailsComponent = (props: JobDetailsComponentProps) => {
  /**
    Component: JobDetailsComponent

    Intended route: /jobs/details?sessionId=<>
    
    */
  const classes = useStyles();
  const query = useQString();
  const sessionId = query.get(SESSION_ID_QSTRING) ?? undefined;
  const prevBatchId = query.get(BATCH_ID_QSTRING) ?? undefined;
  // Not enforced here - just changes request style
  const rawAdminMode: string | undefined =
    query.get(DETAIL_ADMIN_MODE_QSTRING) ?? undefined;
  const adminMode: boolean = rawAdminMode ? rawAdminMode === "true" : false;

  // Helper function to wrap response in root display div
  const rootDisplay = (content: JSX.Element) => {
    return (
      <div className={classes.root}>
        <Stack spacing={2}>
          <JobNavigationComponent
            prevBatchId={prevBatchId}
            adminMode={adminMode}
          />
          {content}
        </Stack>
      </div>
    );
  };

  if (!sessionId) {
    return rootDisplay(
      <p>
        Invalid path, no {SESSION_ID_QSTRING} query string provided. Return{" "}
        <a href="/">home</a>.
      </p>,
    );
  }

  return rootDisplay(
    <SingleJobDetailsComponent
      sessionId={sessionId!}
      refetchOnError={false}
      showIO={true}
      key={sessionId!}
      adminMode={adminMode}
    ></SingleJobDetailsComponent>,
  );
};
