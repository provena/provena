import SearchIcon from "@mui/icons-material/Search";
import { useQuery } from "@tanstack/react-query";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";

import {
    Button,
    CircularProgress,
    Divider,
    FormControl,
    Grid,
    IconButton,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import { DataGrid, GridColDef, GridRowsProp } from "@mui/x-data-grid";

// Custom render for handles in data grid
import {
    renderHandleIdLink,
    searchOnlyDataToolbar,
} from "../components/DataGridHelpers";

import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useLoadedSearch } from "react-libs";
import { getCSVTemplate } from "../queries/ingest";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        FormTextFields: {
            padding: "10px",
        },
    })
);

interface WorkflowTemplateListGridRow {
    id: string;
    displayName: string;
}

interface WorkflowTemplateListProps {
    //workflowTemplateResponse: ModelRunWorkflowTemplateListResponse;
    templateId: string | undefined;
    setTemplateId: (id: string | undefined) => void;
}
const WorkflowTemplateList = observer((props: WorkflowTemplateListProps) => {
    /**
     * Component: WorkflowTemplateList
     *   1. Query the Registry API for a list of Workflow Templates
     *   2. Allow the user to select a row
     */
    const defaultRowsPerPage = 5;
    const tableHeight = 450;
    const [pageSize, setPageSize] = useState<number>(defaultRowsPerPage);

    // Search query
    const [query, setQuery] = useState<string>("");

    //this uses a custom react hook query
    const searchResults = useLoadedSearch({
        subtype: "MODEL_RUN_WORKFLOW_TEMPLATE",
        searchQuery: query,
    });

    const searchSection = (
        <FormControl>
            <Typography mb={"15px"} variant={"subtitle1"}>
                Enter a search query to search for a registered workflow
                template. Select the desired template from the results.
            </Typography>
            <Grid container>
                <Grid item flexGrow={1}>
                    <TextField
                        label="Search for a workflow template"
                        fullWidth
                        value={query}
                        onChange={(event) => {
                            setQuery(event.target.value);
                        }}
                    />
                </Grid>
                <Grid
                    item
                    container
                    xs={1}
                    alignItems="center"
                    justifyContent={"center"}
                >
                    <IconButton>
                        {searchResults.loading ? (
                            <CircularProgress />
                        ) : (
                            <SearchIcon />
                        )}
                    </IconButton>
                </Grid>
            </Grid>
        </FormControl>
    );

    var gridSection: JSX.Element = <></>;

    if (searchResults.error) {
        gridSection = (
            <p>
                An error occured, error:{" "}
                {searchResults.errorMessage ?? "Unknown error."}.
            </p>
        );
    } else if (!searchResults.error) {
        const items = (searchResults.data ?? [])
            .filter((result) => {
                return result.item !== undefined;
            })
            .map((r) => {
                return r.item!;
            });

        const columns: GridColDef[] = [
            {
                field: "id",
                headerName: "ID",
                width: 150,
                renderCell: renderHandleIdLink,
            },
            { field: "displayName", headerName: "Name", flex: 1 },
        ];
        const rows: GridRowsProp = items
            // Make a standard interface from group items and pull out
            // membership
            .map((modelWorkflowTemplate) => {
                return {
                    // create unique string id combination
                    id: modelWorkflowTemplate.id,
                    displayName: modelWorkflowTemplate.display_name,
                } as WorkflowTemplateListGridRow;
            });

        gridSection = (
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
                                const selected =
                                    newSelectionModel as Array<string>;

                                if (selected.length === 1) {
                                    props.setTemplateId(selected[0]);
                                } else {
                                    props.setTemplateId(undefined);
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

    return (
        <div>
            <Stack spacing={2}>
                {searchSection}
                {gridSection}
            </Stack>
        </div>
    );
});

interface GetCSVTemplateProps {
    selected: string;
    clearSelected: () => void;
    downloaded: boolean;
    setDownloaded: (downloaded: boolean) => void;
}
const GetCSVTemplate = observer((props: GetCSVTemplateProps) => {
    /**
     * Component: GetCSVTemplate
     *
     */

    const { isError, error, isSuccess, isFetching } = useQuery({
        queryKey: [props.selected],
        queryFn: () => getCSVTemplate(props.selected),
        enabled: props.downloaded,
    });

    const isDownloadedContent = (
        <Grid
            container
            xs={12}
            spacing={3}
            justifyContent="flex-start"
            alignItems="center"
        >
            <Grid item xs={12}>
                Your CSV template has been downloaded.
            </Grid>
            <Grid item>
                <Button
                    variant="outlined"
                    color="warning"
                    onClick={() => {
                        props.setDownloaded(false);
                    }}
                >
                    Download again
                </Button>
            </Grid>
        </Grid>
    );

    const requiresDownloadContent = (
        <Grid
            container
            xs={12}
            justifyContent="flex-start"
            spacing={2}
            alignContent="center"
        >
            <Grid item>Click here to download the CSV template:</Grid>
            <Grid item>
                <Button
                    variant="outlined"
                    color="success"
                    onClick={() => {
                        props.setDownloaded(true);
                    }}
                >
                    Click to download
                </Button>
            </Grid>
        </Grid>
    );

    return (
        <Grid item xs={12}>
            {isFetching ? (
                <CircularProgress></CircularProgress>
            ) : isError ? (
                <React.Fragment>
                    An error occurred while requesting a CSV template, error
                    message: {error}.
                </React.Fragment>
            ) : props.downloaded && isSuccess ? (
                isDownloadedContent
            ) : (
                requiresDownloadContent
            )}
        </Grid>
    );
});

interface GenerateTemplateProps {}
const GenerateTemplate = observer((props: GenerateTemplateProps) => {
    /**
    Component: GenerateCSVTemplate
    1. Specify a model run workflow template
    2. Lodge the template
    3. Download response
    */
    const [templateId, setTemplateId] = useState<string | undefined>(undefined);
    const [downloaded, setDownloaded] = useState<boolean>(false);

    return (
        <Grid container xs={12} rowGap={1.5}>
            <Grid item xs={12}>
                <Typography variant="h6">
                    Generate a CSV template from a selected workflow template
                </Typography>
            </Grid>
            <Grid item xs={12}>
                <WorkflowTemplateList
                    templateId={templateId}
                    setTemplateId={(id: string | undefined) => {
                        setTemplateId(id);
                        setDownloaded(false);
                    }}
                />
            </Grid>
            {
                // Show the following part if template ID selected
            }
            {templateId !== undefined && (
                <React.Fragment>
                    <Grid item xs={12}>
                        <Divider />
                    </Grid>
                    <Grid item xs={12}>
                        <GetCSVTemplate
                            selected={templateId}
                            clearSelected={() => {
                                setTemplateId(undefined);
                            }}
                            downloaded={downloaded}
                            setDownloaded={setDownloaded}
                        ></GetCSVTemplate>
                    </Grid>
                </React.Fragment>
            )}
        </Grid>
    );
});

export default GenerateTemplate;
