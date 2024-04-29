import { DataGrid, GridColDef, GridRowsProp } from "@mui/x-data-grid";
import { useState } from "react";
import { HistoryEntryAny } from "../provena-interfaces/RegistryModels";
import { Theme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { parseTime } from "../util/util";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    boldRow: {
      fontWeight: "bold",
    },
    normalRow: {},
  }),
);

interface VersionSelectorGridRow {
  id: string;
  time: string;
  username: string;
  reason: string;
}

interface VersionsDataGridSelectorComponentProps {
  history: Array<HistoryEntryAny>;
  currentId?: number;
  selected?: number;
  setSelectedId: (historyId?: number) => void;
}
export const VersionsDataGridSelectorComponent = (
  props: VersionsDataGridSelectorComponentProps,
) => {
  /**
    Component: VersionsDataGridSelectorComponent
    
    Handles the selection of a historical item version
    */

  const classes = useStyles();

  // This id will have '(current)' postfix
  var highlightedId = props.currentId;
  if (highlightedId === undefined && props.history.length > 0) {
    // Non empty list - assume latest is current
    highlightedId = props.history[0].id;
  }

  const defaultRowsPerPage = 5;
  const tableHeight = 400;
  const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);

  const items = props.history;
  const columns: GridColDef[] = [
    {
      field: "id",
      headerName: "ID",
      flex: 3,
    },
    { field: "time", headerName: "Time", flex: 27 },
    { field: "username", headerName: "Username", flex: 20 },
    { field: "reason", headerName: "Reason", flex: 50 },
  ];
  const rows: GridRowsProp = items
    // Make a standard interface from group items and pull out
    // membership
    .map((historyEntry) => {
      return {
        id: historyEntry.id.toString(),
        // Nicely formatted time
        time: parseTime(historyEntry.timestamp),
        username: historyEntry.username,
        reason: historyEntry.reason,
      } as VersionSelectorGridRow;
    });
  return (
    <div style={{ height: tableHeight, width: "100%" }}>
      <DataGrid
        pageSize={pageSize}
        getRowClassName={(params) => {
          if (params.id == highlightedId) {
            return classes.boldRow;
          } else {
            return classes.normalRow;
          }
        }}
        disableColumnFilter
        disableColumnSelector
        disableDensitySelector
        rowsPerPageOptions={[5, 10, 20]}
        onPageSizeChange={(size) => {
          setPageSize(size);
        }}
        componentsProps={{
          toolbar: {
            showQuickFilter: true,
            quickFilterProps: { debounceMs: 500 },
          },
        }}
        onSelectionModelChange={(newSelectionModel) => {
          const selected = newSelectionModel as Array<string>;
          if (selected.length === 1) {
            props.setSelectedId(Number(selected[0]));
          }
        }}
        columns={columns}
        rows={rows}
      ></DataGrid>
    </div>
  );
};
