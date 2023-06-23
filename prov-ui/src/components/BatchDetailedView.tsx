import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
    Grid,
    Button,
    CircularProgress,
    Stack,
    Typography,
    Popover,
} from "@mui/material";
import { describeBatch } from "../queries/ingest";

// Data grid helper funcs
import {
    renderHandleIdLink,
    searchOnlyDataToolbar,
} from "../components/DataGridHelpers";

import { DataGrid, GridRowsProp, GridColDef } from "@mui/x-data-grid";
import { DescribeBatchResponse } from "../shared-interfaces/ProvenanceAPI";

interface DataGridJobRow {
    // Job ID
    id: string;

    // Model run record ID
    recordId: string;

    status: string;
    errorInfo: string;
}

interface BatchJobDetailedViewProps {
    batchId: string;
}

const BatchDetailedView = observer((props: BatchJobDetailedViewProps) => {
    /**
     * Component: BatchJobDetailedView
     *
     */
    // display a live updated table with the status of the batch items
    const { isError, data, error, isSuccess, isFetching, refetch } = useQuery({
        queryKey: [props.batchId],
        queryFn: () => describeBatch(props.batchId),
    });

    // From https://mui.com/x/react-data-grid/components/#cell

    // This references the element to anchor the popover onto
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    // This is the text to contain within the popover
    const [value, setValue] = useState("");

    const handlePopoverClose = () => {
        setAnchorEl(null);
    };

    const open = Boolean(anchorEl);

    const defaultRowsPerPage = 5;
    const tableHeight = 450;
    const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);

    if (isFetching && data === undefined) {
        return (
            <Stack direction="column" alignItems="center">
                <CircularProgress />;
            </Stack>
        );
    }

    if (isSuccess) {
        const info = data as DescribeBatchResponse;
        const allSuccess = info.all_successful;

        const columns: GridColDef[] = [
            {
                field: "id",
                headerName: "Job ID",
                width: 300,
            },
            {
                field: "recordId",
                headerName: "ID",
                width: 150,
                renderCell: renderHandleIdLink,
            },
            { field: "status", headerName: "Job Status", width: 100 },
            { field: "errorInfo", headerName: "Error Info", flex: 1 },
        ];
        const rows: GridRowsProp = info
            .job_info! // Make a standard interface from group items and pull out
            // membership
            .map((job) => {
                return {
                    // Job ID
                    id: job.id,
                    status: job.job_status,
                    errorInfo: job.error_info ?? "",
                    recordId: job.model_run_record_id ?? "",
                } as DataGridJobRow;
            });

        const hoverField = "errorInfo";
        const handlePopoverOpen = (event: React.MouseEvent<HTMLElement>) => {
            const field = event.currentTarget.dataset.field!;
            if (field === hoverField) {
                const id = event.currentTarget.parentElement!.dataset.id!;
                const row = rows.find((r) => r.id === id)!;
                const val = row[field];
                if (val !== "") {
                    setValue(row[field]);
                    setAnchorEl(event.currentTarget);
                }
            }
        };

        // Render a data grid with the jobs and status
        return (
            <Stack spacing={2}>
                <Grid
                    container
                    justifyContent="space-between"
                    alignItems="center"
                >
                    <Grid item>
                        {isFetching ? (
                            <CircularProgress />
                        ) : (
                            <Button
                                onClick={() => {
                                    refetch();
                                }}
                                variant="contained"
                                color="success"
                            >
                                Refresh
                            </Button>
                        )}
                    </Grid>
                    {allSuccess ? (
                        <Grid item xs={3}>
                            <Typography variant="subtitle1">
                                All jobs in this batch succeeded!
                            </Typography>
                        </Grid>
                    ) : (
                        <React.Fragment>
                            {info.missing && info.missing.length > 0 && (
                                <Grid item xs={3}>
                                    <Typography variant="subtitle1">
                                        There are {info.missing?.length} queued
                                        entries. Please wait...
                                    </Typography>
                                </Grid>
                            )}
                            <Grid item xs={3}>
                                <Typography variant="subtitle1">
                                    This batch has errors or is pending
                                    completion, see below.
                                </Typography>
                            </Grid>
                        </React.Fragment>
                    )}
                </Grid>
                <div style={{ height: tableHeight, width: "100%" }}>
                    <DataGrid
                        pageSize={pageSize}
                        disableColumnFilter
                        disableColumnSelector
                        disableSelectionOnClick
                        disableDensitySelector
                        rowsPerPageOptions={[5, 10, 20]}
                        onPageSizeChange={(size) => {
                            setPageSize(size);
                        }}
                        components={{ Toolbar: searchOnlyDataToolbar }}
                        componentsProps={{
                            cell: {
                                onMouseEnter: handlePopoverOpen,
                                onMouseLeave: handlePopoverClose,
                            },
                            toolbar: {
                                showQuickFilter: true,
                                quickFilterProps: { debounceMs: 500 },
                            },
                        }}
                        columns={columns}
                        rows={rows}
                    ></DataGrid>
                    <Popover
                        sx={{
                            pointerEvents: "none",
                        }}
                        open={open}
                        anchorEl={anchorEl}
                        anchorOrigin={{
                            vertical: "bottom",
                            horizontal: "left",
                        }}
                        transformOrigin={{
                            vertical: "top",
                            horizontal: "left",
                        }}
                        onClose={handlePopoverClose}
                        disableRestoreFocus
                    >
                        <div style={{ width: 400 }}>
                            <Typography sx={{ p: 1 }}>{value}</Typography>
                        </div>
                    </Popover>
                </div>
            </Stack>
        );
    }

    if (isError) {
        return (
            <p>
                An error occurred while fetching the batch job status. Error:{" "}
                {error}
            </p>
        );
    }

    return <p>Please wait...</p>;
});

export default BatchDetailedView;
