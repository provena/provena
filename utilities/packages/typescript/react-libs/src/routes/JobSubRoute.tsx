import { Route, Switch } from "react-router-dom";
import { JOB_LIST_ROUTE, JobListComponent } from "./Jobs/JobList";
import {
  JOB_BATCH_ROUTE,
  JOB_DETAILS_ROUTE,
  JobBatchComponent,
  JobDetailsComponent,
} from "./Jobs";

export const JOB_ROUTE_PREFIX = "/jobs";
interface JobSubRouteComponentProps {}
export const JobSubRouteComponent = (props: JobSubRouteComponentProps) => {
  /**
    Component: JobSubRouteComponent

    Router switch for job sub routes
    
    */
  return (
    <Switch>
      <Route path={JOB_LIST_ROUTE}>
        <JobListComponent></JobListComponent>
      </Route>
      <Route path={JOB_DETAILS_ROUTE}>
        <JobDetailsComponent></JobDetailsComponent>
      </Route>
      <Route path={JOB_BATCH_ROUTE}>
        <JobBatchComponent></JobBatchComponent>
      </Route>
    </Switch>
  );
};
