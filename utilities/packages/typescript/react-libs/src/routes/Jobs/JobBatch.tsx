import { Button, Stack, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import React, { useState } from "react";
import {
    DETAIL_ADMIN_MODE_QSTRING,
    JobNavigationComponent,
    useQString,
} from "../..";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            backgroundColor: theme.palette.common.white,
            padding: theme.spacing(3),
            borderRadius: 5,
        },
    })
);

import { CircularProgress, Grid, Popover } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { JOB_DETAILS_ROUTE, SESSION_ID_QSTRING, describeBatch } from "../..";

// Data grid helper funcs
import {
    renderHandleIdLink,
    renderJobStatus,
    searchOnlyDataToolbar,
} from "../..";

import {
    DataGrid,
    GridColDef,
    GridRowsProp,
    GridSelectionModel,
} from "@mui/x-data-grid";
import { useHistory } from "react-router-dom";
import { ProvLodgeModelRunResult } from "../../shared-interfaces/AsyncJobModels";

interface DataGridJobRow {
    // Job ID
    id: string;

    status: string;
    errorInfo: string;
}

export interface BatchJobDetailedViewProps {
    batchId: string;
    onJobSelected: (id: string) => void;
    adminMode: boolean;
}

export const BatchDetailedView = (props: BatchJobDetailedViewProps) => {
    /**
     * Component: BatchJobDetailedView
     *
     * display a live updated table with the status of the batch items. Also
     * enables selection of a focussed node which can be used by parent
     */

    // Every 3 seconds
    const basePollInterval = 5000;
    const { isError, data, error, isSuccess, isFetching, refetch } = useQuery({
        queryKey: [props.batchId],
        queryFn: () =>
            describeBatch({
                batchId: props.batchId,
                limit: 100,
                adminMode: props.adminMode,
            }),
        // Conditional refetch if incomplete items
        refetchInterval: (data, _) => {
            if (
                data?.jobs.some((val) => {
                    // Are there any jobs incomplete?
                    return ["FAILED", "SUCCEEDED"].indexOf(val.status) === -1;
                })
            ) {
                return basePollInterval;
            } else {
                return false;
            }
        },
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

    const defaultRowsPerPage = 10;
    const tableHeight = 700;
    const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);

    const onSelection = (newSelectionModel: GridSelectionModel) => {
        const selected = newSelectionModel as Array<string>;
        if (selected.length === 1) {
            const id = selected[0];
            props.onJobSelected(id);
        }
    };

    if (isFetching && data === undefined) {
        return (
            <Stack direction="column" alignItems="center">
                <CircularProgress />;
            </Stack>
        );
    }

    if (isSuccess) {
        const allSuccess = data.jobs.every((val) => {
            return val.status === "SUCCEEDED";
        });
        const isPending = data.jobs.some((val) => {
            return val.status !== "SUCCEEDED" && val.status !== "FAILED";
        });
        const hasErrors = data.jobs.some((val) => {
            return val.status === "FAILED";
        });

        const columns: GridColDef[] = [
            {
                field: "id",
                headerName: "Session ID",
                width: 300,
            },
            {
                field: "status",
                headerName: "Job Status",
                width: 150,
                renderCell: renderJobStatus,
            },
            { field: "errorInfo", headerName: "Error Info", flex: 1 },
        ];
        const rows: GridRowsProp = data.jobs
            // Make a standard interface from group items and pull out
            // membership
            .map((job) => {
                var recordId = "";
                if (job.status === "SUCCEEDED") {
                    if (job.job_sub_type === "MODEL_RUN_PROV_LODGE") {
                        const result =
                            job.result as unknown as ProvLodgeModelRunResult;
                        recordId = result.record.id;
                    }
                }
                return {
                    // Job ID
                    id: job.session_id,
                    status: job.status,
                    errorInfo: job.status === "FAILED" ? job.info ?? "" : "",
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
                    ) : hasErrors ? (
                        <Grid item xs={3}>
                            <Typography variant="subtitle1">
                                This batch contains jobs which did not finish
                                successfully.
                            </Typography>
                        </Grid>
                    ) : (
                        isPending && (
                            <React.Fragment>
                                <Grid item xs={3}>
                                    <Typography variant="subtitle1">
                                        This batch is pending completion, see
                                        below.
                                    </Typography>
                                </Grid>
                            </React.Fragment>
                        )
                    )}
                </Grid>
                <div style={{ height: tableHeight, width: "100%" }}>
                    <DataGrid
                        pageSize={pageSize}
                        disableColumnFilter
                        disableColumnSelector
                        disableDensitySelector
                        onSelectionModelChange={onSelection}
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
};

export default BatchDetailedView;

export const BATCH_ID_QSTRING = "batchId";
export const BATCH_ADMIN_MODE_QSTRING = "adminMode";
export const JOB_BATCH_ROUTE = "/jobs/batch";
export interface JobBatchComponentProps {}
export const JobBatchComponent = (props: JobBatchComponentProps) => {
    /**
    Component: JobBatchComponent

    Intended route: /jobs/batch?batchId=<>
    
    */
    const classes = useStyles();
    const history = useHistory();

    const query = useQString();
    const batchId = query.get(BATCH_ID_QSTRING) ?? undefined;

    // Not enforced here - just changes request style
    const rawAdminMode: string | undefined =
        query.get(BATCH_ADMIN_MODE_QSTRING) ?? undefined;
    const adminMode: boolean = rawAdminMode ? rawAdminMode === "true" : false;

    // Helper function to wrap response in root display div
    const rootDisplay = (content: JSX.Element) => {
        return (
            <div className={classes.root}>
                <Stack spacing={2}>
                    <JobNavigationComponent adminMode={adminMode} />
                    {content}
                </Stack>
            </div>
        );
    };

    if (!batchId) {
        return rootDisplay(
            <p>
                Invalid path, no {BATCH_ID_QSTRING} query string provided.
                Return <a href="/">home</a>.
            </p>
        );
    }

    const onSelection = (id: string) => {
        history.push(
            JOB_DETAILS_ROUTE +
                `?${SESSION_ID_QSTRING}=${id}&${BATCH_ID_QSTRING}=${batchId}&${DETAIL_ADMIN_MODE_QSTRING}=${adminMode.toString()}`
        );
    };

    return rootDisplay(
        <BatchDetailedView
            batchId={batchId}
            onJobSelected={onSelection}
            adminMode={adminMode}
        />
    );
};
