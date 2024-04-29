import {
  Button,
  Dialog,
  DialogActions,
  Stack,
  Theme,
  Typography,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import {
  DataGrid,
  GridColDef,
  GridRenderCellParams,
  GridRowsProp,
} from "@mui/x-data-grid";
import React, { useState } from "react";
import {
  CopyableLinkedHandleComponent,
  ReleaseActionText,
  ReleasedStatusText,
  releaseStateStylePicker,
  renderApprovalActionStatus,
  renderCellTextExpand,
  renderNameAndIdById,
  timestampToLocalTime,
} from "react-libs";
import {
  ItemDataset,
  ItemSubType,
  ReleaseHistoryEntry,
} from "react-libs/provena-interfaces/RegistryAPI";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      padding: theme.spacing(4),
      borderRadius: 5,
      backgroundColor: theme.palette.common.white,
      width: "100%",
      minHeight: "80vh",
    },
    datasetInfoRow: {
      width: "100%",
      alignItems: "center",
    },
    boldRow: {
      fontWeight: "bold",
    },
  }),
);

interface ApprovalsHistoryDataGridRow {}

interface ApprovalsHistoryDialogProps {
  dialogOpen: boolean;
  // Used in parent to control dialog close
  setDialogOpen: (dialogOpen: boolean) => void;
  dataset: ItemDataset;
}

export const ApprovalsHistoryDialog = (props: ApprovalsHistoryDialogProps) => {
  /**
    Component: ApprovalsHistoryDialog
    
    Popup dialog to show the history of release action
    */

  const classes = useStyles();

  const releaseHistory = props.dataset.release_history;

  // Set data grid table
  const defaultPageSize: number = 10;
  const [pageSize, setPageSize] = useState<number>(defaultPageSize);

  interface ReleaseHistoryDataRow {
    actionStatus: ReleaseActionText | ReleasedStatusText;
    timestamp: number;
    actor: string;
    note: string;
  }

  const columns: GridColDef[] = [
    {
      field: "actionStatus",
      headerName: "Action",
      width: 125,
      renderCell: renderApprovalActionStatus,
    },
    {
      field: "timestamp",
      headerName: "Created Time",
      width: 225,
      filterable: false,
      valueFormatter: (params) => {
        return timestampToLocalTime(params.value);
      },
    },
    {
      field: "actor",
      type: "actions",
      headerAlign: "left",
      align: "left",
      headerName: "Actor",
      width: 180,
      renderCell: (params: GridRenderCellParams) =>
        renderNameAndIdById({
          params,
          subtype: "PERSON" as ItemSubType,
        }),
    },
    {
      field: "note",
      headerName: "Note",
      flex: 1,
      minWidth: 100,
      renderCell: (params: GridRenderCellParams) =>
        renderCellTextExpand({ params, initialCharNum: 200 }),
    },
  ];

  const rows: GridRowsProp<ReleaseHistoryDataRow> = !!releaseHistory
    ? releaseHistory.map((row: ReleaseHistoryEntry) => {
        // Determine if the action is from requester or approver
        var actorId = "";

        // Row is for requester
        if (row.action === "REQUEST") {
          actorId = row.requester ?? "";
        }

        // Row is for approver
        if (row.action === "APPROVE" || row.action === "REJECT") {
          actorId = row.approver;
        }

        const actionStatusTextOverride = releaseStateStylePicker(
          row.action,
        ).text;

        return {
          actionStatus: actionStatusTextOverride,
          // Return number here, will render to local time in cell render later
          timestamp: row.timestamp,
          // Return id here, will render name in cell render later
          actor: actorId,
          note: row.notes ?? "",
        };
      })
    : [];

  // Handlers

  // Close dialog
  const handleCloseOnClick = () => {
    props.setDialogOpen(false);
  };

  return (
    <React.Fragment>
      {props.dialogOpen && (
        <Dialog
          open={props.dialogOpen}
          fullWidth
          maxWidth="lg"
          onClose={(event, reason) => {
            if (reason !== "backdropClick") handleCloseOnClick();
          }}
        >
          <Stack direction="column" className={classes.root} spacing={4}>
            {/* Title */}
            <Typography variant="h4">Approvals History</Typography>
            {/* Current dataset info */}
            <Stack
              direction="row"
              spacing={1}
              className={classes.datasetInfoRow}
            >
              <Typography variant="h6">{`Current dataset: ${props.dataset.display_name} - `}</Typography>
              <CopyableLinkedHandleComponent handleId={props.dataset.id} />
            </Stack>
            {/* Data Grid */}
            <DataGrid
              //Set unique key for each row
              getRowId={(row) =>
                row?.timestamp + row?.actionStatus + row?.actor
              }
              columns={columns}
              rows={rows}
              disableSelectionOnClick
              pageSize={pageSize}
              disableColumnFilter
              disableColumnSelector
              disableDensitySelector
              rowsPerPageOptions={[5, 10, 20]}
              onPageSizeChange={(size) => {
                setPageSize(size);
              }}
              getEstimatedRowHeight={() => 100}
              getRowHeight={() => "auto"}
              sx={{
                // From https://stackoverflow.com/questions/74624999/how-to-make-material-ui-datagrid-row-cliccable-and-with-pointer-cursor-withou
                // disable cell selection style
                ".MuiDataGrid-cell:focus": {
                  outline: "none",
                },
              }}
              // Default sorting, latest records first
              initialState={{
                sorting: {
                  sortModel: [{ field: "timestamp", sort: "desc" }],
                },
              }}
            />
            {/* Page action buttons */}
            <DialogActions>
              <Button variant="contained" onClick={handleCloseOnClick}>
                Close
              </Button>
            </DialogActions>
          </Stack>
        </Dialog>
      )}
    </React.Fragment>
  );
};
