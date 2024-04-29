import {
  Button,
  CircularProgress,
  FormControlLabel,
  Grid,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import {
  DataGrid,
  GridColDef,
  GridRowsProp,
  GridSelectionModel,
} from "@mui/x-data-grid";
import React, { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import {
  BATCH_ID_QSTRING,
  JOB_BATCH_ROUTE,
  JOB_DETAILS_ROUTE,
  SESSION_ID_QSTRING,
  timestampToLocalTime,
  useGenericPaginatedList,
  listJobs,
  useAccessCheck,
  DETAIL_ADMIN_MODE_QSTRING,
  BATCH_ADMIN_MODE_QSTRING,
  useQueryStringVariable,
  JobWakerComponent,
} from "../../";
import {
  JobStatus,
  JobStatusTable,
  JobSubType,
  ListJobsResponse,
} from "../../provena-interfaces/AsyncJobAPI";
import {
  renderJobStatus,
  searchOnlyDataToolbar,
} from "../../util/DataGridHelpers";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      backgroundColor: theme.palette.common.white,
      padding: theme.spacing(3),
      borderRadius: 5,
    },
  }),
);

type GroupJobState = "IN_PROGRESS" | "SUCCEEDED" | "FAILED";
interface GroupedJobRow {
  batchId: string;
  entries: Array<JobStatusTable>;
  groupStatus: GroupJobState;
}
interface SingleJobRow extends JobStatusTable {}
interface GroupedJobs {
  // Which type is this?
  isGroup: boolean;
  isSingle: boolean;

  // Data for either type
  groupRow?: GroupedJobRow;
  singleRow?: SingleJobRow;

  // Username
  username: string;
}

interface JobGrouperInput {
  jobs: Array<JobStatusTable>;
}
function jobGrouper(inputs: JobGrouperInput): Array<GroupedJobs> {
  /**
    Function: JobGrouper
    
    Takes a flat list of jobs and groups by batch for visualisation
    */

  const groupedRows: Array<GroupedJobs> = [];

  for (const row of inputs.jobs) {
    const batchId = row.batch_id;

    if (!!batchId) {
      // Does this group exist?
      var groupedEntry = groupedRows.find((entry) => {
        return entry.isGroup && entry.groupRow?.batchId === batchId;
      });

      if (groupedEntry !== undefined) {
        var gRow = groupedEntry.groupRow;
        if (gRow === undefined) {
          throw new Error("Group row should contain group entry.");
        }

        // Proper group row
        gRow.entries.push(row);

        // Update status
        if (row.status !== "SUCCEEDED") {
          // Succeeded never modifies state - check others
          if (row.status === "FAILED") {
            // Mark as failed
            gRow.groupStatus = "FAILED";
          }
          // Otherwise must be in some sort of pending state - doesn't override error
          else if (gRow.groupStatus !== "FAILED") {
            gRow.groupStatus = "IN_PROGRESS";
          }
        }
      } else {
        // New group
        var baseStatus: GroupJobState = "IN_PROGRESS";

        // Succeeded maps to success
        if (row.status === "SUCCEEDED") {
          baseStatus = "SUCCEEDED";
          // Failed maps to failed
        } else if (row.status === "FAILED") {
          baseStatus = "FAILED";
        }
        // All other states are in progress
        var newGRow = {
          batchId,
          groupStatus: baseStatus,
          entries: [JSON.parse(JSON.stringify(row))],
        } as GroupedJobRow;

        groupedRows.push({
          isGroup: true,
          isSingle: false,
          groupRow: newGRow,
          username: row.username,
        });
      }
    } else {
      // Single entry - no batch
      groupedRows.push({
        isGroup: false,
        isSingle: true,
        singleRow: JSON.parse(JSON.stringify(row)) as SingleJobRow,
        username: row.username,
      });
    }
  }

  return groupedRows;
}

interface BatchJobRow {
  id: string;
  username: string;

  createdTime: string;
  // Which type is this?
  isGroup: boolean;
  isSingle: boolean;

  batchId?: string;
  sessionId?: string;

  // only present if group
  jobCount?: number;

  // Special type referring to standalone/batch
  jobType: string;

  jobSubType: JobSubType;

  // Either Group status or single job status
  status: JobStatus | GroupJobState;
}

interface JobListDisplayComponentProps {
  onSelectStandaloneDetail: (id: string) => void;
  onSelectBatchDetail: (id: string) => void;
  adminMode: boolean;
}
const JobListDisplayComponent = (props: JobListDisplayComponentProps) => {
  /**
    Component: JobListDisplayComponent

    Displays a selectable data grid job list
    
    */
  const fetchPageSize = 10;

  // Paginated query for user jobs
  // TODO use useInfiniteQuery instead
  const paginatedUserJobs = useGenericPaginatedList<
    JobStatusTable,
    ListJobsResponse
  >({
    pagerFunction(paginationKey, limit) {
      return listJobs({
        limit,
        paginationKey,
        adminMode: props.adminMode,
      });
    },
    itemExtractFunction(loadedItem) {
      return loadedItem.jobs;
    },
    queryKey: "userlistjobs",
    fetchOnStart: true,
    limit: fetchPageSize,
  });

  // If the admin mode toggles, then reset the query
  useEffect(() => {
    paginatedUserJobs.resetList();
  }, [props.adminMode]);

  const groupedRows =
    paginatedUserJobs.records !== undefined
      ? jobGrouper({ jobs: paginatedUserJobs.records })
      : undefined;

  // Display a data grid selector
  const defaultRowsPerPage = fetchPageSize;
  const tableHeight = 700;
  const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);

  // Only show global loading symbol when there is no data + loading state
  if (paginatedUserJobs.loading && paginatedUserJobs.records === undefined) {
    return <CircularProgress />;
  }

  if (paginatedUserJobs.error) {
    return (
      <p>
        An error occurred while fetching user history -{" "}
        {paginatedUserJobs.errorMessage ?? "No error provided"}.
      </p>
    );
  }

  if (groupedRows !== undefined) {
    if (groupedRows.length === 0) {
      return <p>No job history.</p>;
    }

    const columns: GridColDef[] = [
      {
        field: "id",
        headerName: "ID",
        width: 300,
      },
      {
        field: "username",
        headerName: "Username",
        width: 200,
      },
      { field: "jobSubType", headerName: "Job Type", flex: 1.5 },
      {
        field: "status",
        headerName: "Status",
        width: 125,
        renderCell: renderJobStatus,
      },
      { field: "jobType", headerName: "Type", width: 100 },
      { field: "jobCount", headerName: "Count", width: 75 },
      { field: "createdTime", headerName: "Created Time", flex: 2 },
    ];

    const rows: GridRowsProp = groupedRows.map((groupedRow) => {
      if (groupedRow.isGroup) {
        const groupData = groupedRow.groupRow!;
        // Group type
        return {
          id: groupData.batchId,
          username: groupedRow.username,
          createdTime: timestampToLocalTime(
            groupData.entries[0].created_timestamp,
          ),
          isGroup: true,
          isSingle: false,
          status: groupData.groupStatus,
          batchId: groupData.batchId,
          jobCount: groupData.entries.length,
          jobType: "Batch",
          jobSubType: groupData.entries[0].job_sub_type,
        } as BatchJobRow;
      } else {
        // Single type
        const singleData = groupedRow.singleRow!;
        return {
          id: singleData.session_id,
          username: groupedRow.username,
          createdTime: timestampToLocalTime(singleData.created_timestamp),
          isGroup: false,
          isSingle: true,
          status: singleData.status,
          sessionId: singleData.session_id,
          jobType: "Standalone",
          jobSubType: singleData.job_sub_type,
        } as BatchJobRow;
      }
    });

    const onSelection = (newSelectionModel: GridSelectionModel) => {
      const selected = newSelectionModel as Array<string>;
      if (selected.length === 1) {
        const id = selected[0];

        const row = groupedRows.find((r) => {
          return (
            (r.isGroup ? r.groupRow!.batchId : r.singleRow!.session_id) === id
          );
        });

        // backout in weird case
        if (row === undefined) {
          return;
        }

        if (row.isGroup) {
          props.onSelectBatchDetail(id);
        } else {
          props.onSelectStandaloneDetail(id);
        }
      }
    };

    return (
      <Grid container xs={12} rowGap={1}>
        <Grid item xs={12}>
          <div style={{ height: tableHeight, width: "100%" }}>
            <DataGrid
              pageSize={pageSize}
              disableColumnFilter
              disableColumnSelector
              disableDensitySelector
              rowsPerPageOptions={[5, 10, 20]}
              onPageSizeChange={(size) => {
                setPageSize(size);
              }}
              components={{ Toolbar: searchOnlyDataToolbar }}
              componentsProps={{
                toolbar: {
                  showQuickFilter: true,
                  quickFilterProps: { debounceMs: 500 },
                },
              }}
              onSelectionModelChange={onSelection}
              columns={columns}
              rows={rows}
              sx={{
                // From https://stackoverflow.com/questions/74624999/how-to-make-material-ui-datagrid-row-cliccable-and-with-pointer-cursor-withou
                // disable cell selection style
                ".MuiDataGrid-cell:focus": {
                  outline: "none",
                },
                // pointer cursor on ALL rows
                "& .MuiDataGrid-row:hover": {
                  cursor: "pointer",
                },
              }}
            ></DataGrid>
          </div>
        </Grid>
        <Grid item xs={12}>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignContent="center"
          >
            <Button
              color="warning"
              onClick={() => {
                paginatedUserJobs.resetList();
              }}
              variant={"contained"}
            >
              Reset
            </Button>
            <Button
              variant={"contained"}
              color="success"
              disabled={!paginatedUserJobs.moreAvailable}
              onClick={() => {
                if (paginatedUserJobs.requestMoreRecords !== undefined) {
                  paginatedUserJobs.requestMoreRecords();
                }
              }}
            >
              Load More
            </Button>
          </Stack>
        </Grid>
      </Grid>
    );
  }
  return <p>Please wait...content is loading.</p>;
};

interface AdminSelectorComponentProps {
  adminMode: boolean;
  toggleAdminMode: () => void;
}
const AdminSelectorComponent = (props: AdminSelectorComponentProps) => {
  /**
    Component: AdminSelectorComponent
    
    Allows the user to toggle admin mode on/off
    */

  return (
    <FormControlLabel
      label="Admin List Mode?"
      control={
        <Switch
          defaultChecked={props.adminMode}
          checked={props.adminMode}
          onChange={props.toggleAdminMode}
        />
      }
    />
  );
};

export const JOB_LIST_ROUTE = "/jobs/list";
export const LIST_ADMIN_MODE_QSTRING = "adminMode";
export interface JobListComponentProps {}
export const JobListComponent = (props: JobListComponentProps) => {
  /**
    Component: JobListComponent

    Intended route: /jobs/list
    
    */
  const classes = useStyles();
  const history = useHistory();

  // Check user permissions
  const adminReadCheck = useAccessCheck({
    componentName: "job-service",
    desiredAccessLevel: "READ",
  });
  const adminWriteCheck = useAccessCheck({
    componentName: "job-service",
    desiredAccessLevel: "WRITE",
  });

  const isJobAdminRead = adminReadCheck.fallbackGranted;
  const isJobAdminWrite = adminWriteCheck.fallbackGranted;

  // Has the user activated admin fetch mode?
  const adminQString = useQueryStringVariable({
    queryStringKey: LIST_ADMIN_MODE_QSTRING,
    defaultValue: "false",
  });

  const adminMode = (adminQString.value ?? "false") === "true";
  const setAdminMode = (adminMode: boolean) => {
    const setter = adminQString.setValue;
    if (!!setter) {
      setter(adminMode ? "true" : "false");
    }
  };

  // Helper function to wrap response in root display div
  const rootDisplay = (content: JSX.Element) => {
    return <div className={classes.root}>{content}</div>;
  };

  // Handlers for clicks
  const onSelectStandaloneDetail = (id: string) => {
    // Open detailed view
    history.push(
      JOB_DETAILS_ROUTE +
        `?${SESSION_ID_QSTRING}=${id}&${DETAIL_ADMIN_MODE_QSTRING}=${adminMode.toString()}`,
    );
  };
  const onSelectBatchDetail = (id: string) => {
    // Open batch view
    history.push(
      JOB_BATCH_ROUTE +
        `?${BATCH_ID_QSTRING}=${id}&${BATCH_ADMIN_MODE_QSTRING}=${adminMode.toString()}`,
    );
  };
  return rootDisplay(
    <Stack spacing={2}>
      <Grid container justifyContent={"space-between"}>
        <Grid item xs={isJobAdminWrite ? 5 : 12}>
          <Typography variant="h6">Job History</Typography>
          <Typography variant="subtitle1">
            Jobs are created during interaction with the system. You can view
            the details of a standalone or batch job, by clicking on the entry
            below. Click the 'Load More' button to fetch more items.
          </Typography>
        </Grid>
        {isJobAdminWrite && (
          <Grid item xs={5}>
            <JobWakerComponent />
          </Grid>
        )}
      </Grid>
      {isJobAdminRead && (
        <React.Fragment>
          <AdminSelectorComponent
            adminMode={adminMode}
            toggleAdminMode={() => {
              setAdminMode(!adminMode);
            }}
          />
        </React.Fragment>
      )}
      <JobListDisplayComponent
        onSelectBatchDetail={onSelectBatchDetail}
        onSelectStandaloneDetail={onSelectStandaloneDetail}
        adminMode={adminMode}
      ></JobListDisplayComponent>
    </Stack>,
  );
};
