import OpenInNew from "@mui/icons-material/OpenInNew";
import OpenInNewOff from "@mui/icons-material/OpenInNewOff";
import SearchIcon from "@mui/icons-material/Search";
import WarningIcon from "@mui/icons-material/Warning";
import {
    Alert,
    Box,
    Button,
    Checkbox,
    CircularProgress,
    FormControl,
    FormControlLabel,
    Grid,
    IconButton,
    InputAdornment,
    InputLabel,
    MenuItem,
    Select,
    Stack,
    TextField,
    Tooltip,
    Typography,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import debounce from "lodash.debounce";
import { observer } from "mobx-react-lite";
import { useCallback, useEffect, useState } from "react";
import {
    useLoadedSearch,
    usePaginatedRecordList,
    useQueryStringVariable,
    useUntypedLoadedItem,
    useUserLinkServiceLookup,
} from "react-libs";
import { registryItemIdHdlLinkResolver } from "util/helper";
import { ItemSubtypeSelector } from "../components/ItemSubtypeSelector";
import ResultCard from "../components/ResultCard";
import { SortOptions, SortType } from "../shared-interfaces/RegistryAPI";
import { ItemBase, ItemSubType } from "../shared-interfaces/RegistryModels";
import accessStore from "../stores/accessStore";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        topPanel: {
            backgroundColor: theme.palette.common.white,
            borderRadius: 5,
            padding: theme.spacing(2),
        },
        floatingLoadMore: {
            position: "relative",
            bottom: "50px",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 1,
        },
        filterPanel: {
            backgroundColor: theme.palette.common.white,
            padding: theme.spacing(2),
            borderRadius: 5,
        },
        searchContainer: {
            marginBottom: theme.spacing(2),
        },
        gridContainer: {
            overflowX: "hidden",
            padding: theme.spacing(1),
            backgroundColor: theme.palette.grey[300],
            borderRadius: 5,
            width: "100%",
            overflowY: "auto",
            height: "60vh",
        },
        gridFlowBoxContainer: {
            display: "grid",
            gridTemplateColumns: `repeat( auto-fill, minmax(280px, 1fr) );`,
        },
        loadingIndicatorContainer: {
            display: "flex",
            flexDirection: "row",
            justifyContent: "center",
            alignItems: "start",
            padding: theme.spacing(5),
        },
    })
);

const displayNameMap: Map<string, SortOptions> = new Map([
    [
        "Created Time (Oldest First)",
        { sort_type: "CREATED_TIME", ascending: true },
    ],
    [
        "Created Time (Newest First)",
        { sort_type: "CREATED_TIME", ascending: false },
    ],
    [
        "Updated Time (Oldest First)",
        { sort_type: "UPDATED_TIME", ascending: true },
    ],
    [
        "Updated Time (Newest First)",
        { sort_type: "UPDATED_TIME", ascending: false },
    ],
    ["Display Name (A-Z)", { sort_type: "DISPLAY_NAME", ascending: true }],
    ["Display Name (Z-A)", { sort_type: "DISPLAY_NAME", ascending: false }],
]);

const sortOptionsMap: Map<string, string> = new Map([
    [
        JSON.stringify({ sort_type: "CREATED_TIME", ascending: true }),
        "Created Time (Oldest First)",
    ],
    [
        JSON.stringify({ sort_type: "CREATED_TIME", ascending: false }),
        "Created Time (Newest First)",
    ],
    [
        JSON.stringify({ sort_type: "UPDATED_TIME", ascending: true }),
        "Updated Time (Oldest First)",
    ],
    [
        JSON.stringify({ sort_type: "UPDATED_TIME", ascending: false }),
        "Updated Time (Newest First)",
    ],
    [
        JSON.stringify({ sort_type: "DISPLAY_NAME", ascending: true }),
        "Display Name (A-Z)",
    ],
    [
        JSON.stringify({ sort_type: "DISPLAY_NAME", ascending: false }),
        "Display Name (Z-A)",
    ],
]);

interface SortOptionsSelectorProps {
    selectedType: SortType;
    setSelectedType: (type: SortType) => void;
    ascending: boolean;
    setAscending: (ascending: boolean) => void;
    disabled?: boolean;
}
const SortOptionsSelector = observer((props: SortOptionsSelectorProps) => {
    /**
    Component: SortOptionsSelector

    Combines the sort type ascending/descending into a single combined selector
    which has customised display names for each combination
    */

    const sortTypeAscendingToDisplayName = (
        sortOptions: SortOptions
    ): string => {
        return (
            sortOptionsMap.get(JSON.stringify(sortOptions)) ??
            "Unknown options. Contact Admin"
        );
    };

    const displayNameToSortOptions = (
        displayName: string
    ): SortOptions | undefined => {
        return displayNameMap.get(displayName);
    };

    const selectOptions: string[] = Array.from(displayNameMap.keys());

    return (
        <Select
            notched={true}
            id="sort-dropdown"
            labelId="sort-label"
            label="Sort by"
            disabled={!!props.disabled}
            value={sortTypeAscendingToDisplayName({
                sort_type: props.selectedType,
                ascending: props.ascending,
            })}
            fullWidth={true}
            onChange={(event) => {
                const selectedSortOptions = displayNameToSortOptions(
                    event.target.value
                );
                if (selectedSortOptions === undefined) {
                    console.log(
                        "User clicked on unexpected displayname in sort type selector: " +
                            event.target.value
                    );
                } else {
                    props.setSelectedType(selectedSortOptions.sort_type!);
                    props.setAscending(selectedSortOptions.ascending!);
                }
            }}
        >
            {selectOptions.map((displayName: string) => {
                return <MenuItem value={displayName}>{displayName}</MenuItem>;
            })}
        </Select>
    );
});

interface FilterPanelProps {
    // Are we filtering by subtype?
    filterSubtype: boolean;
    setFilterSubtype: (filterSubtype: boolean) => void;
    filterSubtypeDisabled?: boolean;

    // Which type?
    selectedItemSubtype: ItemSubType;
    setSelectedItemSubtype: (itemSubtype: ItemSubType) => void;
    selectSubtypeDisabled?: boolean;

    // Sort type?
    selectedSortType: SortType;
    setSelectedSortType: (sortType: SortType) => void;
    ascending: boolean;
    setAscending: (ascending: boolean) => void;
    selectedSortTypeDisabled?: boolean;

    // Search query
    searchQuery: string;
    setSearchQuery: (query: string) => void;
}
const FilterAndSearchPanel = observer((props: FilterPanelProps) => {
    /**
    Component: FilterPanel

    NOTE that this uses Grid2 since there were some bugs in grid one making the
    layout not align properly 
    */
    const classes = useStyles();

    // Input handle id for opening item in a new page
    const [textfieldInputHandleId, setTextfieldInputHandleId] =
        useState<string>("");
    // Handle id save for query, undefined for not querying on mount
    const [queryHandleId, setQueryHandleId] = useState<string | undefined>(
        undefined
    );

    // Check item id is valid before go to the new page
    const untypedLoadedItem = useUntypedLoadedItem({
        id: queryHandleId,
        enabled: true,
    });

    // Debounce query handle id setting
    const debounceTimeout = 500;
    const debouncedSetQueryHandleId = useCallback(
        debounce(setQueryHandleId, debounceTimeout),
        []
    );

    // Validate input handle id with debounced setting
    useEffect(() => {
        if (textfieldInputHandleId !== "") {
            debouncedSetQueryHandleId(textfieldInputHandleId);
        } else {
            debouncedSetQueryHandleId(undefined);
        }
    }, [textfieldInputHandleId]);

    // Handlers

    const onOpenNewPageClick = (
        event: React.MouseEvent<HTMLButtonElement, MouseEvent>
    ) => {
        event.preventDefault();
        // Open item page if id is valid
        if (!!untypedLoadedItem.data?.id) {
            window.open(
                registryItemIdHdlLinkResolver(untypedLoadedItem.data.id),
                "_blank",
                "noopener,noreferrer"
            );
        } else {
            console.error(
                "Error: Handle id is undefined. No handle id returned from validation."
            );
        }
    };

    // JSX Element

    // Button for opening new page based on handle id
    const openNewPageEndAdornment: JSX.Element = (
        <InputAdornment position="end">
            <Tooltip
                title={
                    untypedLoadedItem.loading
                        ? "Validating input handle id..."
                        : untypedLoadedItem.success
                        ? "Click to open the item page based on the entered ID."
                        : untypedLoadedItem.error
                        ? untypedLoadedItem.errorMessage ??
                          "No error message provided."
                        : false
                }
            >
                <Box>
                    <IconButton
                        aria-label="Open page for item handle id"
                        disabled={!untypedLoadedItem.success}
                        onClick={onOpenNewPageClick}
                        edge="end"
                    >
                        {untypedLoadedItem.success ? (
                            <OpenInNew color="success" />
                        ) : (
                            <OpenInNewOff />
                        )}
                    </IconButton>
                </Box>
            </Tooltip>
        </InputAdornment>
    );

    return (
        <Grid2 container className={classes.filterPanel} spacing={1}>
            <Grid2 xs={3}>
                <FormControl fullWidth>
                    <InputLabel id="sort-label" shrink={true}>
                        Sort by
                    </InputLabel>
                    <SortOptionsSelector
                        selectedType={props.selectedSortType}
                        setSelectedType={props.setSelectedSortType}
                        disabled={!!props.selectedSortTypeDisabled}
                        ascending={props.ascending}
                        setAscending={props.setAscending}
                    ></SortOptionsSelector>
                </FormControl>
            </Grid2>
            <Grid2 xs={3}>
                <FormControl fullWidth>
                    <ItemSubtypeSelector
                        disabled={
                            !props.filterSubtype ||
                            !!props.selectSubtypeDisabled
                        }
                        selectedItemSubType={props.selectedItemSubtype}
                        onChange={props.setSelectedItemSubtype}
                        listType="FILTERABLE"
                        subtitle={"Item Subtype"}
                    ></ItemSubtypeSelector>
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={props.filterSubtype}
                                onChange={() => {
                                    props.setFilterSubtype(
                                        !props.filterSubtype
                                    );
                                }}
                                disabled={!!props.filterSubtypeDisabled}
                            ></Checkbox>
                        }
                        label={"Filter by type?"}
                    />
                </FormControl>
            </Grid2>
            <Grid2 flexGrow={1} padding={0} margin={0}>
                <Grid2>
                    <FormControl fullWidth>
                        <TextField
                            id="search-input"
                            label="Search for registry items"
                            value={props.searchQuery}
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <SearchIcon />
                                    </InputAdornment>
                                ),
                            }}
                            onChange={(event) => {
                                props.setSearchQuery(
                                    event.target.value as string
                                );
                            }}
                        />
                    </FormControl>
                </Grid2>
                <Stack
                    direction="row"
                    columnGap={2}
                    padding={"4px"}
                    alignItems="center"
                    justifyContent="end"
                >
                    <Typography>Or:</Typography>
                    <FormControl>
                        <TextField
                            id="item-handle-id-input"
                            label="Enter item ID"
                            onChange={(event) => {
                                event.preventDefault();
                                setTextfieldInputHandleId(
                                    event.target.value as string
                                );
                            }}
                            value={textfieldInputHandleId}
                            error={
                                untypedLoadedItem.error &&
                                textfieldInputHandleId !== ""
                            }
                            InputProps={{
                                endAdornment: openNewPageEndAdornment,
                            }}
                        />
                    </FormControl>
                </Stack>
            </Grid2>
        </Grid2>
    );
});

const Records = observer(() => {
    const classes = useStyles();
    const { keycloak, initialized } = useKeycloak();

    useEffect(() => {
        accessStore.checkAccess();
    }, [keycloak.authenticated]);

    const accessReady = !!accessStore.readAccess;

    // By default sort on updated time and filter on dataset
    const defaultSort: SortType = "UPDATED_TIME";
    const defaultAscending = false;
    const defaultItemSubType: ItemSubType = "DATASET";

    // Check user link service
    const userLink = useUserLinkServiceLookup({});
    const userPersonId: string | undefined = userLink.data;
    const determineIsUser = (item: ItemBase) => {
        return item.id === userPersonId && item.item_subtype === "PERSON";
    };

    // ============================================================
    // Query string managed state for sorting, filtering and search
    // ============================================================

    // Are we filtering?
    const { value: filterSubtypeQ, setValue: setFilterSubtypeQ } =
        useQueryStringVariable({
            queryStringKey: "filtering",
            defaultValue: "false",
        });

    const filterSubtype = filterSubtypeQ === "true";
    const setFilterSubtype = (filterSubtype: boolean): void => {
        if (filterSubtype) {
            setFilterSubtypeQ!("true");
        } else {
            setFilterSubtypeQ!("false");
        }
    };

    // Selected subtype
    const { value: selectedSubtypeQ, setValue: setSelectedSubtype } =
        useQueryStringVariable({
            queryStringKey: "subtype",
            defaultValue: defaultItemSubType,
        });
    const selectedSubtype = selectedSubtypeQ as ItemSubType;

    // Selected sort type - managed with query string arg
    const { value: selectedSortTypeQ, setValue: setSelectedSortType } =
        useQueryStringVariable({
            queryStringKey: "sortType",
            defaultValue: defaultSort,
        });
    const selectedSortType = selectedSortTypeQ as SortType;

    // Ascending?
    const { value: sortAscendingQ, setValue: setAscendingQ } =
        useQueryStringVariable({
            queryStringKey: "ascending",
            defaultValue: defaultAscending ? "true" : "false",
        });

    const sortAscending = sortAscendingQ === "true";
    const setSortAscending = (sortAscending: boolean): void => {
        if (sortAscending) {
            setAscendingQ!("true");
        } else {
            setAscendingQ!("false");
        }
    };

    // Search query - query string arg
    const { value: searchQuery, setValue: setSearchQuery } =
        useQueryStringVariable({
            queryStringKey: "query",
            defaultValue: "",
        });

    const searching = searchQuery !== "";

    // ===================================
    // Search and results incl. pagination
    // ===================================

    // Search results
    const searchResults = useLoadedSearch({
        searchQuery: searchQuery,
        enabled: accessReady,
        subtype: filterSubtype ? selectedSubtype : undefined,
    });

    // Use a list of paginated records
    const pageSize = 10;
    const {
        records: listRecords,
        requestMoreRecords,
        moreAvailable,
        loading,
        error,
        errorMessage,
    } = usePaginatedRecordList({
        sortBy: { sort_type: selectedSortType, ascending: sortAscending },
        filterBy: filterSubtype ? { item_subtype: selectedSubtype } : undefined,
        pageSize: pageSize,
        fetchOnStart: true,
        enabled: accessReady && !searching,
    });

    const records: ItemBase[] | undefined = searching
        ? searchResults.data
              ?.filter((result) => {
                  return result.item !== undefined;
              })
              .map((result) => {
                  return result.item!;
              })
        : listRecords;

    // Show a complete loading icon?
    const totalLoading = (loading || searchResults.loading) && !records;

    // Show a partial load spinner
    const partialLoading = (loading || searchResults.loading) && !totalLoading;

    // Error conditions
    const accessError = accessStore.error;
    const accessErrorMessage = accessStore.errorMessage ?? "Unknown";
    const insufficientAccess =
        !accessError && !accessReady && !accessStore.loading;

    const registryError = searchResults.error || error;
    const registryErrorMessage =
        (searchResults.error && searchResults.errorMessage) ||
        (error && errorMessage) ||
        "Unknown";

    const errorContent = insufficientAccess ? (
        // Access loaded but was insufficient
        <Grid container item xs={12} className={classes.gridContainer}>
            <Grid
                sx={{
                    width: "100%",
                    paddingTop: "48px",
                    paddingBottom: "48px",
                    backgroundColor: "white",
                    borderRadius: "5px",
                    textAlign: "center",
                }}
            >
                <WarningIcon sx={{ fontSize: "96px" }} />
                <Alert
                    sx={{
                        width: "75%",
                        marginLeft: "auto",
                        marginRight: "auto",
                        marginBottom: "32px",
                    }}
                    severity="warning"
                    action={
                        <Button variant="outlined" href="/profile">
                            Request Access
                        </Button>
                    }
                >
                    You do not have sufficient registry store permissions to
                    view registry entities.
                </Alert>
                <Button variant="outlined" href="/">
                    Return to Landing Page
                </Button>
            </Grid>
        </Grid>
    ) : // Access error
    accessError ? (
        <Grid
            container
            direction="column"
            sx={{
                justifyContent: "center",
                alignItems: "center",
                backgroundColor: "white",
                borderRadius: "5px",
            }}
            padding={2}
        >
            <WarningIcon
                sx={{
                    fontSize: "96px",
                    marginBottom: "16px",
                }}
            />
            <Typography sx={{ marginBottom: "24px" }}>
                An error occurred while determining access to the registry.
            </Typography>
            <Alert
                variant="outlined"
                severity="warning"
                sx={{ width: "75%", marginBottom: "24px" }}
            >
                {accessErrorMessage}
            </Alert>
            <Typography sx={{ marginBottom: "24px" }}>
                Please try again later.
            </Typography>
            <Button variant="outlined" href="/">
                Return to Landing Page
            </Button>
        </Grid>
    ) : // Registry error
    registryError ? (
        <Grid
            container
            direction="column"
            sx={{
                justifyContent: "center",
                alignItems: "center",
                backgroundColor: "white",
                borderRadius: "5px",
            }}
            padding={2}
        >
            <WarningIcon
                sx={{
                    fontSize: "96px",
                    marginBottom: "16px",
                }}
            />
            <Typography sx={{ marginBottom: "24px" }}>
                An error occurred while loading items in the registry.
            </Typography>
            <Alert
                variant="outlined"
                severity="warning"
                sx={{ width: "75%", marginBottom: "24px" }}
            >
                {registryErrorMessage}
            </Alert>
            <Typography sx={{ marginBottom: "24px" }}>
                Please try again later.
            </Typography>
            <Button variant="outlined" href="/">
                Return to Landing Page
            </Button>
        </Grid>
    ) : null;

    return (
        <Stack spacing={2}>
            <Grid
                container
                justifyContent="space-between"
                className={classes.topPanel}
            >
                <Typography variant="h5">Explore Registered Entries</Typography>
                <Button variant="contained" href="/registerentity">
                    Register an Entity
                </Button>
            </Grid>
            {errorContent}
            {accessStore.readAccess ? (
                <FilterAndSearchPanel
                    filterSubtype={filterSubtype}
                    setFilterSubtype={setFilterSubtype}
                    selectedItemSubtype={selectedSubtype}
                    setSelectedItemSubtype={setSelectedSubtype!}
                    selectedSortType={selectedSortType}
                    ascending={sortAscending}
                    setAscending={setSortAscending}
                    selectedSortTypeDisabled={searching}
                    setSelectedSortType={setSelectedSortType!}
                    searchQuery={searchQuery!}
                    setSearchQuery={setSearchQuery!}
                />
            ) : null}
            {totalLoading ? (
                <Grid
                    container
                    item
                    xs={12}
                    className={classes.loadingIndicatorContainer}
                >
                    <CircularProgress />
                </Grid>
            ) : (
                <div style={{ width: "100%" }}>
                    <Grid
                        container
                        item
                        xs={12}
                        flexDirection={"row"}
                        className={`${classes.gridContainer} ${classes.gridFlowBoxContainer}`}
                    >
                        {records && records.length > 0 ? (
                            records?.map((i) => (
                                <ResultCard
                                    key={i.id}
                                    cardDetails={i}
                                    isUser={determineIsUser(i)}
                                />
                            ))
                        ) : (
                            <p>No results.</p>
                        )}
                    </Grid>
                    {partialLoading && (
                        <Grid item container xs={12} justifyContent="center">
                            <CircularProgress />
                        </Grid>
                    )}
                    {!searching && moreAvailable && !partialLoading && (
                        // This is a floating button always displayed in the
                        // grid div
                        <Button
                            variant="contained"
                            onClick={requestMoreRecords}
                            className={classes.floatingLoadMore}
                        >
                            Load more...
                        </Button>
                    )}
                </div>
            )}
        </Stack>
    );
});

export default Records;
