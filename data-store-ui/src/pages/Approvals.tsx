import {
  Alert,
  AlertTitle,
  Box,
  Button,
  CircularProgress,
  Stack,
  Theme,
  Tooltip,
  Typography,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import {
  DataGrid,
  GridCallbackDetails,
  GridColDef,
  GridRenderCellParams,
  GridRowParams,
  GridRowsProp,
  GridToolbar,
  MuiEvent,
} from "@mui/x-data-grid";
import { useKeycloak } from "@react-keycloak/web";
import { ApprovalsHistoryDialog } from "components/ApprovalsHistoryDialog";
import { useEffect, useState } from "react";
import {
  ReleaseActionText,
  ReleasedStatusText,
  UseUserLinkServiceLookupOutput,
  listApprovalRequests,
  releaseStateStylePicker,
  renderApprovalActionStatus,
  renderCellButton,
  renderCellTextExpand,
  renderDatasetCombinedNameAndId,
  renderNameAndIdById,
  timestampToLocalTime,
  useGenericPaginatedList,
  useUserLinkServiceLookup,
} from "react-libs";
import {
  ItemDataset,
  ItemSubType,
  PaginatedDatasetListResponse,
  ReleaseHistoryEntry,
} from "react-libs/provena-interfaces/RegistryAPI";
import {
  datasetApprovalTakeActionLinkResolver,
  datasetApprovalsTabLinkResolver,
} from "util/helper";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      padding: theme.spacing(4),
      borderRadius: 5,
      backgroundColor: theme.palette.common.white,
      width: "100%",
      minHeight: "100vh",
    },
    actionButtons: {
      width: "100%",
      justifyContent: "center",
    },
    // Data grid list
    dataGrid: {
      width: "100%",
    },
    // Other useful layout
    fullWidth: { width: "100%" },
    tbPaddings: {
      paddingTop: theme.spacing(2),
      paddingBottom: theme.spacing(2),
    },
    lrPadding: {
      paddingLeft: theme.spacing(2),
      paddingRight: theme.spacing(2),
    },
  }),
);

interface ApprovalRequestsListRow {
  actionStatus?: ReleaseActionText | ReleasedStatusText;
  // Request created time
  timestamp?: number;
  // Dataset info
  // use for history dialog as well
  dataset: ItemDataset;

  // latest requester
  requester?: string;
  // Latest note from both requester and reviewer
  latestNote?: string;
}

// Extract function for useGenericPaginatedList hook.
const approvalsRequestExtractFunction = (
  loadedItem: PaginatedDatasetListResponse,
): ApprovalRequestsListRow[] => {
  const resArray: ApprovalRequestsListRow[] = !!loadedItem.dataset_items
    ? loadedItem.dataset_items.map((item: ItemDataset) => {
        // If release history is  undefined
        const releaseHistory = item.release_history;
        if (!releaseHistory || releaseHistory.length <= 0) {
          console.error(
            "There is no release history for this dataset:" + item.id,
          );
          return {
            // return dataset details
            dataset: item,
          };
        }

        // Reversed history to get latest info first
        const releaseHistoryCopy = JSON.parse(
          JSON.stringify(releaseHistory),
        ) as ReleaseHistoryEntry[];

        const latestFirstHistory = releaseHistoryCopy.reverse();

        const latestReleaseHistory = releaseHistoryCopy[0];

        // If currently action is requested, then show requester ID, if rejected or approved, show the latest requester ID
        const latestRequester =
          latestReleaseHistory.requester ??
          latestFirstHistory.find((release) => !!release.requester)?.requester;

        const actionStatusTextOverride = releaseStateStylePicker(
          latestReleaseHistory.action,
        ).text;

        // else
        return {
          actionStatus: actionStatusTextOverride,
          // return number here, will render to local time in cell render later
          timestamp: item.release_timestamp,
          // Dataset info
          dataset: item,
          // Name is rendered by id in cell render late.
          requester: latestRequester,
          latestNote: latestReleaseHistory.notes,
        };
      })
    : [];

  return resArray;
};

export const Approvals = () => {
  /**
    Component: Approvals

    The page is for listing all the approvals for current user, include requested approvals, rejected approvals and approved approvals
    */

  const classes = useStyles();

  // const history = useHistory();

  // Get users info
  const { keycloak } = useKeycloak();

  // Get id from current user name
  const userLink: UseUserLinkServiceLookupOutput = useUserLinkServiceLookup({
    username: keycloak.tokenParsed?.preferred_username,
  });

  const userLinkedId = userLink.data as string;

  // Data grid table columns render

  // Set data grid table
  const defaultPageSize: number = 5;
  const [pageSize, setPageSize] = useState<number>(defaultPageSize);

  // Dataset's history dialog popup when double clicked on data grid row
  const [selectedDataset, setSelectedDataset] = useState<
    ItemDataset | undefined
  >(undefined);
  const [historyDialogOpen, setHistoryDialogOpen] = useState<boolean>(false);

  // For cleaning
  const cleanStates = () => {
    setSelectedDataset(undefined);
    setHistoryDialogOpen(false);
  };

  useEffect(() => {
    return cleanStates();
  }, []);

  const columns: GridColDef[] = [
    {
      field: "actionStatus",
      headerName: "Action",

      // Fixed width
      width: 125,

      renderCell: renderApprovalActionStatus,
    },
    {
      field: "timestamp",
      headerName: "Latest Update",

      // Fixed width
      width: 225,
      filterable: false,
      valueFormatter: (params) => {
        return timestampToLocalTime(params.value);
      },
    },
    {
      field: "dataset",
      type: "actions",
      headerAlign: "left",
      align: "left",
      headerName: "Dataset",
      width: 180,
      renderCell: renderDatasetCombinedNameAndId,
    },
    {
      field: "requester",
      type: "actions",
      headerAlign: "left",
      align: "left",
      headerName: "Requested By",
      width: 180,
      renderCell: (params: GridRenderCellParams) =>
        renderNameAndIdById({
          params,
          subtype: "PERSON" as ItemSubType,
        }),
    },
    {
      field: "latestNote",
      headerName: "Latest Note",
      flex: 1.5,
      minWidth: 100,
      renderCell: (params: GridRenderCellParams) =>
        renderCellTextExpand({ params, initialCharNum: 200 }),
    },
    {
      field: "takeAction",
      type: "actions",
      headerAlign: "left",
      headerName: "Take Action",
      width: 160,
      renderCell: (params: GridRenderCellParams) =>
        renderCellButton({
          text: "Take Action",
          link: datasetApprovalTakeActionLinkResolver(params.row.dataset.id),
          disabled: params.row.actionStatus !== "REQUESTED",
          tooltipText:
            "You've already taken action on this dataset's approval request",
          buttonVariant: "contained",
          className: classes.actionButtons,
        }),
    },
    {
      field: "viewDataset",
      type: "actions",
      headerAlign: "left",
      headerName: "View Dataset",
      width: 160,
      renderCell: (params: GridRenderCellParams) =>
        renderCellButton({
          text: "View Dataset",
          link: datasetApprovalsTabLinkResolver(params.row.dataset.id),
          disabled: false,
          buttonVariant: "contained",
          className: classes.actionButtons,
        }),
    },
  ];

  const approvalRequestsPaginatedList = useGenericPaginatedList<
    ApprovalRequestsListRow,
    PaginatedDatasetListResponse
  >({
    pagerFunction(paginationKey) {
      return listApprovalRequests({
        pagination_key: paginationKey,
        page_size: 10,
        sort_by: { sort_type: "RELEASE_TIMESTAMP", ascending: false },
        filter_by: {
          release_reviewer: userLinkedId,
          // Show all request for now
          // release_status: "PENDING",
        },
      });
    },
    itemExtractFunction: approvalsRequestExtractFunction,
    queryKey: "approvalRequestsList",
    fetchOnStart: true,
    enabled: !!userLinkedId,
    limit: 10,
  });

  // Data grid table rows
  const rows: GridRowsProp<ApprovalRequestsListRow> =
    approvalRequestsPaginatedList.records ?? [];

  // Handler

  // on row double clicked
  const onRowDoubleClickHandler = (
    params: GridRowParams,
    event: MuiEvent<React.MouseEvent>,
    details: GridCallbackDetails,
  ) => {
    // Use double click to open dataset history dialog,
    // Single click only for link actions and button actions.

    const dataset = params.row.dataset;

    if (!!dataset) {
      setSelectedDataset(dataset);
      setHistoryDialogOpen(true);
    }
  };

  // Status

  // Loading
  if (approvalRequestsPaginatedList.loading) {
    return (
      <Stack direction="column" className={classes.root} spacing={4}>
        <Typography variant="h4">Approval Requests</Typography>
        <Stack
          direction="row"
          spacing={2}
          alignItems="center"
          className={classes.fullWidth}
        >
          <CircularProgress />{" "}
          <Typography>Please wait...content is loading.</Typography>
        </Stack>
      </Stack>
    );
  }

  // Error
  if (approvalRequestsPaginatedList.error) {
    return (
      <Stack direction="column" className={classes.root} spacing={4}>
        <Typography variant="h4">Approval Requests</Typography>
        <Alert variant="outlined" severity="error">
          <AlertTitle>
            Error: An error occurred when fetching approvals.
          </AlertTitle>
          {approvalRequestsPaginatedList.errorMessage ??
            "Error message is not provided."}
        </Alert>
      </Stack>
    );
  }

  // No approvals for current user
  const NoRowsOverlayText = () => (
    <Stack
      height="100%"
      width="100%"
      alignItems="center"
      justifyContent="center"
    >
      There are no datasets currently awaiting your review.
    </Stack>
  );

  return (
    <Stack direction="column" className={classes.root} spacing={4}>
      <Typography variant="h4">Approvals</Typography>
      {/* Page description */}
      <Typography variant="body1">
        This page lists all the datasets for which you are the requested
        reviewer. You can <strong>double click</strong> a row to view more
        details about the approval history of the dataset you clicked on. You
        can click 'Take Action' to respond to the request.
      </Typography>
      {/* Data grid table for listing all the approvals */}
      <DataGrid
        //Set unique key for each row
        getRowId={(row) =>
          row?.timestamp + row?.requester + row?.dataset.id + row?.actionStatus
        }
        columns={columns}
        rows={rows}
        pageSize={pageSize}
        // disableColumnFilter
        // disableColumnSelector
        disableDensitySelector
        rowsPerPageOptions={[5, 10, 20]}
        onPageSizeChange={(size) => {
          setPageSize(size);
        }}
        onRowDoubleClick={onRowDoubleClickHandler}
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
        getEstimatedRowHeight={() => 200}
        getRowHeight={() => "auto"}
        components={{
          Toolbar: GridToolbar,
          NoRowsOverlay: NoRowsOverlayText,
        }}
        componentsProps={{
          toolbar: {
            csvOptions: { disableToolbarButton: true },
            printOptions: { disableToolbarButton: true },
            showQuickFilter: false,
          },
        }}
        className={classes.dataGrid}
      />
      {/* Load More Button */}
      <Stack
        direction="row"
        spacing={2}
        className={classes.fullWidth}
        justifyContent="end"
      >
        <Tooltip
          title={
            !approvalRequestsPaginatedList.moreAvailable
              ? "No more records remain."
              : ""
          }
        >
          <Box>
            <Button
              variant={"contained"}
              disabled={!approvalRequestsPaginatedList.moreAvailable}
              onClick={() => {
                if (approvalRequestsPaginatedList.moreAvailable) {
                  approvalRequestsPaginatedList.requestMoreRecords();
                }
              }}
            >
              Load More
            </Button>
          </Box>
        </Tooltip>
      </Stack>
      {/* Open history details dialog when double clicked dataset row */}
      {historyDialogOpen && !!selectedDataset && (
        <ApprovalsHistoryDialog
          dialogOpen={historyDialogOpen}
          setDialogOpen={setHistoryDialogOpen}
          dataset={selectedDataset}
        />
      )}
    </Stack>
  );
};
