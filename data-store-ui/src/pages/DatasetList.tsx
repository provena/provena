import {
    Backdrop,
    Button,
    CircularProgress,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    FormControl,
    Grid,
    InputLabel,
    Pagination,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { observer } from "mobx-react-lite";
import React, { useEffect, useState } from "react";
import { LANDING_PAGE_LINK_PROFILE } from "react-libs";
import { Link } from "react-router-dom";
import BreadcrumbLinks from "../components/BreadcrumbLinks";
import { DatasetSearchLinked } from "../components/DatasetSearchBox";
import DatasetSummary from "../components/DatasetSummary";
import { OrganisationFilterDisplay } from "../components/OrganisationFilterDisplay";
import { SortOptionsSelector } from "../components/SortSelector";
import { usePaginatedRecordList } from "react-libs";
import { useSearchQueryString } from "../hooks/searchQueryString";
import { useLoadedSearch } from "react-libs";
import { useOrganisationFilter } from "../hooks/useOrganisationFilter";
import { SortType } from "../shared-interfaces/RegistryAPI";
import { ItemDataset } from "../shared-interfaces/DataStoreAPI";
import accessStore from "../stores/accessStore";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            display: "flex",
            flexWrap: "wrap",
            flexFlow: "column",
            padding: theme.spacing(4),
            backgroundColor: "white",
            borderRadius: 5,
            minHeight: "80vh",
        },
        button: {
            marginRight: theme.spacing(1),
        },
        instructions: {
            marginTop: theme.spacing(1),
            marginBottom: theme.spacing(1),
        },
        paginationMargin: {
            marginTop: theme.spacing(2),
            marginBottom: theme.spacing(2),
        },
        gridMargin: {
            marginTop: theme.spacing(4),
        },
    })
);

const getPageCount = (items: number, pageSize: number): number => {
    return Math.max(1, Math.ceil(items / pageSize));
};

const DatasetList = observer(() => {
    const classes = useStyles();
    const { keycloak } = useKeycloak();

    // Firstly - make sure we have access
    useEffect(() => {
        accessStore.checkAccess();
    }, [keycloak.authenticated]);

    const readyToFetch =
        keycloak.authenticated &&
        (accessStore.forceErrorBypass ||
            ((accessStore.readAccess ?? false) && !accessStore.error));

    // Sorting - type and asecnding
    const defaultSortType: SortType = "UPDATED_TIME";
    const defaultAscending: boolean = false;
    const [sortSelection, setSortSelection] =
        useState<SortType>(defaultSortType);
    const [ascending, setAscending] = useState<boolean>(defaultAscending);

    // Two possible lists

    // Pagination state
    const [currentPage, setCurrentPage] = useState<number>(1);
    const displayPageSize = 10;

    // 1) explore view
    // Manage the dataset list using the paginated hook
    const fetchPageSize = 10;

    // Update this function as we increase page count
    const paginatedDatasetList = usePaginatedRecordList({
        pageSize: fetchPageSize,
        enabled: readyToFetch,
        filterBy: { item_subtype: "DATASET", record_type: "COMPLETE_ONLY" },
        sortBy: { sort_type: sortSelection, ascending: ascending },
        // When more records are loaded, set the current page to the last
        // available and scroll to top of list
        onMoreLoaded(records) {
            const pageCount = getPageCount(records.length, displayPageSize);
            setCurrentPage(pageCount);
            window.scrollTo(0, 0);
        },
    });

    // 2) search view

    // this is an auto debounced search manager

    // This is a query string managed parameter
    const { searchQuery, setSearchQuery } = useSearchQueryString({});
    const searchResults = useLoadedSearch({
        searchQuery: searchQuery,
        subtype: "DATASET",
    });

    // Using search?
    const usingSearch = searchQuery.length > 0;

    // ----------------------------------

    // Which list to use?
    var relevantRecords: ItemDataset[] | undefined =
        paginatedDatasetList.records === undefined
            ? undefined
            : (paginatedDatasetList.records as ItemDataset[]);
    if (usingSearch) {
        relevantRecords = searchResults.data
            ?.filter((r) => {
                return !r.loading && r.item !== undefined;
            })
            .map((r) => {
                return r.item! as unknown as ItemDataset;
            });
    }

    // Which error/message/loading are we concerned about?
    var isError: boolean = paginatedDatasetList.error;
    var errorMessage: string | undefined = paginatedDatasetList.errorMessage;
    var loading: boolean = paginatedDatasetList.loading;
    if (usingSearch) {
        isError = searchResults.error;
        errorMessage = searchResults.errorMessage;
        loading = searchResults.loading;
    }

    // Handle organisation filtering and display
    const filteredByOrg = useOrganisationFilter({
        datasets: relevantRecords ?? [],
    });

    // If the sort options/direction change, clear any organisation filters selected
    useEffect(() => {
        filteredByOrg.clearOrganisations();
    }, [sortSelection, ascending]);

    // Derive the desired datasets to display
    const filteredDatasets: ItemDataset[] = filteredByOrg.filteredDatasets;
    const recordCount = filteredDatasets.length;

    // Work out spliced range, page count etc
    const pageCount = getPageCount(recordCount, displayPageSize);

    // Keep current page bounded
    useEffect(() => {
        if (currentPage > pageCount) {
            setCurrentPage(pageCount);
        }
    }, [currentPage, pageCount]);

    const splicedDatasets = filteredDatasets.slice(
        (currentPage - 1) * displayPageSize,
        displayPageSize * currentPage
    );

    // Define the error dialog fragment in case something goes wrong with the
    // access check process
    const dialogFragment = (
        <React.Fragment>
            {
                //Error dialogue based on store state
            }
            <Dialog open={accessStore.error}>
                <DialogTitle> Access check error! </DialogTitle>
                <DialogContent>
                    <DialogContent>
                        <p>
                            The system experienced an issue while trying to
                            check your system access. <br />
                            Error message:{" "}
                            {accessStore.errorMessage ??
                                "No error message provided."}
                            <br />
                            Press <i>Dismiss</i> to attempt loading from the
                            data store anyway. If you are definitely authorised
                            and still see this error, please use the{" "}
                            <i>Contact Us</i> link to report an issue.
                        </p>
                    </DialogContent>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => accessStore.dismissError()}>
                        Dismiss
                    </Button>
                </DialogActions>
            </Dialog>
        </React.Fragment>
    );

    const registerFragment =
        accessStore.forceErrorBypass || accessStore.writeAccess ? (
            <Button
                color="primary"
                variant="contained"
                component={Link}
                to="new_dataset"
                id="dataset-registration-button"
            >
                Register Dataset
            </Button>
        ) : // Show nothing (no button)
        // if registration is not available
        null;

    const breadcrumbLinks = [
        {
            link: "/",
            label: "Home",
        },
        {
            link: "/datasets",
            label: "Datasets",
        },
    ];

    // Backdrop loading
    var showGlobalLoading: boolean = false;
    if (usingSearch) {
        showGlobalLoading = accessStore.loading;
    } else {
        showGlobalLoading =
            (loading && splicedDatasets.length === 0) || accessStore.loading;
    }

    // Result list loading - always show when loading
    const resultListLoading: boolean = loading;

    if (showGlobalLoading) {
        return (
            <div className={classes.root}>
                <BreadcrumbLinks links={breadcrumbLinks} />
                <Backdrop open={true}>
                    <CircularProgress />
                </Backdrop>
                {dialogFragment}
            </div>
        );
    }

    // display dataset list if read access is allowed
    // or if error override was forced
    if (accessStore.forceErrorBypass || accessStore.readAccess) {
        return (
            <div className={classes.root}>
                <BreadcrumbLinks links={breadcrumbLinks} />
                <Grid container>
                    <Grid xs={3}>
                        {/* Left Filter */}
                        <OrganisationFilterDisplay
                            organisationIdList={filteredByOrg.organisations}
                            count={filteredByOrg.organisationCounts}
                            filteredCount={filteredByOrg.filteredCount}
                            selectedOrganisations={
                                filteredByOrg.selectedOrganisations
                            }
                            addOrganisation={filteredByOrg.selectOrganisation}
                            removeOrganisation={
                                filteredByOrg.deselectOrganisation
                            }
                        />
                    </Grid>
                    <Grid xs={9}>
                        <Grid container justifyContent="space-between">
                            {
                                //  Conditionally display the register
                                //  dataset button
                            }
                            <Grid item xs={3}>
                                <FormControl fullWidth disabled={usingSearch}>
                                    <InputLabel id="sort-label" shrink={true}>
                                        Sort by
                                    </InputLabel>
                                    <SortOptionsSelector
                                        selectedType={sortSelection}
                                        setSelectedType={setSortSelection}
                                        ascending={ascending}
                                        setAscending={setAscending}
                                        disabled={usingSearch}
                                    ></SortOptionsSelector>
                                </FormControl>
                            </Grid>
                            <Grid item>
                                <div style={{ minHeight: "50px" }}>
                                    {resultListLoading && <CircularProgress />}
                                </div>
                            </Grid>
                            <Grid item>{registerFragment}</Grid>
                        </Grid>
                        <Grid className={classes.gridMargin}>
                            <DatasetSearchLinked
                                query={searchQuery}
                                setQuery={setSearchQuery}
                                needClearIcon={true}
                            />
                        </Grid>
                        <Grid className={classes.gridMargin}>
                            {splicedDatasets.length > 0 ? (
                                <>
                                    {splicedDatasets.map((ele) => (
                                        <DatasetSummary
                                            key={ele.id}
                                            dataset={ele}
                                        ></DatasetSummary>
                                    ))}
                                    {!usingSearch &&
                                        paginatedDatasetList.moreAvailable && (
                                            <Grid
                                                container
                                                justifyContent="center"
                                                style={{ marginTop: "20px" }}
                                            >
                                                <Grid item>
                                                    {paginatedDatasetList.loading ? (
                                                        <CircularProgress />
                                                    ) : (
                                                        <Button
                                                            onClick={() => {
                                                                paginatedDatasetList.requestMoreRecords();
                                                            }}
                                                            variant="contained"
                                                        >
                                                            Load More
                                                        </Button>
                                                    )}
                                                </Grid>
                                            </Grid>
                                        )}
                                </>
                            ) : (
                                <Grid container justifyContent={"center"}>
                                    <Grid item>
                                        {resultListLoading ? (
                                            <p>Loading...</p>
                                        ) : (
                                            <p>No records to show...</p>
                                        )}
                                    </Grid>
                                </Grid>
                            )}
                        </Grid>

                        <Grid className={classes.gridMargin}>
                            <Pagination
                                count={pageCount}
                                page={currentPage}
                                onChange={(e, page) => {
                                    if (page <= pageCount) {
                                        setCurrentPage(page);
                                    } else {
                                        setCurrentPage(pageCount);
                                    }
                                }}
                                showFirstButton
                                showLastButton
                            />
                        </Grid>
                        <Grid className={classes.gridMargin}></Grid>
                    </Grid>
                </Grid>
                {dialogFragment}
            </div>
        );
    }
    // display message explaining access error if not allowed
    else {
        return (
            <div className={classes.root}>
                <BreadcrumbLinks links={breadcrumbLinks} />
                <Grid container>
                    <Grid xs={12}>
                        <Grid className={classes.gridMargin}>
                            <h3>Unauthorised</h3>
                            <p>
                                You have insufficient permissions to use the
                                data store registry. You can manage your roles
                                at{" "}
                                <a href={LANDING_PAGE_LINK_PROFILE}>
                                    Landing Portal.
                                </a>
                            </p>
                        </Grid>
                    </Grid>
                </Grid>
                {dialogFragment}
            </div>
        );
    }
});

export default DatasetList;
