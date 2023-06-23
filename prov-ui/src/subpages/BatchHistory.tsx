import { observer } from "mobx-react-lite";
import { useState } from "react";

import { useQuery } from "@tanstack/react-query";

import {
    Button,
    CircularProgress,
    Divider,
    Grid,
    Stack,
    Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { getBatchJobHistory } from "../queries/ingest";
import { BatchHistoryResponse } from "../shared-interfaces/ProvenanceAPI";

// Data grid helper funcs
import { searchOnlyDataToolbar } from "../components/DataGridHelpers";

import {
    DataGrid,
    GridColDef,
    GridRowsProp,
    GridSelectionModel,
} from "@mui/x-data-grid";
import BatchDetailedView from "../components/BatchDetailedView";
import RegenerateCSV from "../components/RegenerateCSV";

const useStyles = makeStyles((theme: Theme) => createStyles({}));

interface DetailedViewProps {
    batchId: string;
    onExit: () => void;
}
const DetailedView = observer((props: DetailedViewProps) => {
    /**
    Component: DetailedView
    */
    const [downloaded, setDownloaded] = useState<boolean>(false);

    return (
        <Stack direction="column" alignItems="stretch" spacing={2}>
            <Stack direction="row" justifyContent="space-between">
                <Button
                    variant="contained"
                    color="warning"
                    onClick={() => {
                        setDownloaded(false);
                        props.onExit();
                    }}
                >
                    Back
                </Button>
                <Typography variant="subtitle1">
                    <b>Batch ID</b>: {props.batchId}
                </Typography>
            </Stack>
            <BatchDetailedView batchId={props.batchId} />
            <Divider orientation="horizontal" flexItem></Divider>
            <RegenerateCSV
                batchId={props.batchId}
                downloaded={downloaded}
                setDownloaded={setDownloaded}
                queryId={props.batchId}
            ></RegenerateCSV>
        </Stack>
    );
});

interface BatchJobRow {
    id: string;
    createdTime: string;
    jobCount: number;
}

interface SelectBatchProps {
    selectedBatchId?: string;
    setSelectedBatchId: (id?: string) => void;
}
const SelectBatch = observer((props: SelectBatchProps) => {
    /*
    Component: SelectBatch
    Selects the batch history by batch ID with a datagrid selector
    */

    // React query manager for users job history
    const { isError, error, isSuccess, isFetching, data } = useQuery({
        queryKey: ["user batch history"],
        queryFn: () => getBatchJobHistory(),
    });

    // Display a data grid selector
    const defaultRowsPerPage = 10;
    const tableHeight = 600;
    const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);

    // data grid multi user selection
    const [selectionModel, setSelectionModel] = useState<GridSelectionModel>(
        []
    );

    if (isFetching) {
        return <CircularProgress />;
    }

    if (isError) {
        return <p>An error occurred while fetching user history - {error}.</p>;
    }

    if (isSuccess) {
        // Data is known at this point
        const history = data as BatchHistoryResponse;
        const batchJobs = history.batch_jobs ?? [];

        if (batchJobs.length === 0) {
            return <p>No batch job history.</p>;
        }

        if (props.selectedBatchId !== undefined) {
            return <p>Selected batch ID {props.selectedBatchId}</p>;
        }
        const columns: GridColDef[] = [
            {
                field: "id",
                headerName: "Batch ID",
                width: 300,
            },
            { field: "createdTime", headerName: "Created Time", flex: 2 },
            { field: "jobCount", headerName: "Job Count", flex: 1 },
        ];

        const formatTimestamp = (timestamp: number) => {
            return new Date(timestamp * 1000).toLocaleString();
        };

        const rows: GridRowsProp = batchJobs.map((batchJob) => {
            return {
                id: batchJob.batch_id,
                createdTime: formatTimestamp(batchJob.created_time),
                jobCount: batchJob.jobs.length,
            } as BatchJobRow;
        });

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
                            onSelectionModelChange={(newSelectionModel) => {
                                setSelectionModel(newSelectionModel);
                                const selected =
                                    newSelectionModel as Array<string>;

                                if (selected.length === 1) {
                                    props.setSelectedBatchId(selected[0]);
                                } else {
                                    props.setSelectedBatchId(undefined);
                                }
                            }}
                            columns={columns}
                            rows={rows}
                        ></DataGrid>
                    </div>
                </Grid>
            </Grid>
        );
    }
    return <p>Please wait...content is loading.</p>;
});

interface BatchHistoryProps {}

const BatchHistory = observer((props: BatchHistoryProps) => {
    /**
     * Component: LodgeTemplate
     *
     */
    const [focusedBatchId, setFocusedBatchId] = useState<string | undefined>(
        undefined
    );
    return (
        <Stack direction="column" spacing={2}>
            {focusedBatchId === undefined ? (
                <SelectBatch
                    selectedBatchId={focusedBatchId}
                    setSelectedBatchId={setFocusedBatchId}
                ></SelectBatch>
            ) : (
                <DetailedView
                    batchId={focusedBatchId}
                    onExit={() => setFocusedBatchId(undefined)}
                />
            )}
        </Stack>
    );
});

export default BatchHistory;
