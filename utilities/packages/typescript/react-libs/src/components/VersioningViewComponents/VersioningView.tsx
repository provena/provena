import HelpOutline from "@mui/icons-material/HelpOutline";
import {
    Alert,
    AlertTitle,
    Box,
    Button,
    CircularProgress,
    Grid,
    Stack,
    Theme,
    Tooltip,
    Typography,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import React, { useEffect, useState } from "react";

import { useHistory } from "react-router-dom";
import "react-vertical-timeline-component/style.min.css";
import {
    DOCUMENTATION_BASE_URL,
    SubtypeHeaderComponent,
    useLoadedVersionList,
} from "../..";
import { LoadedEntity } from "../../interfaces";
import { ItemBase } from "../../shared-interfaces/RegistryAPI";
import { Swatch, assignIcon, getSwatchForSubtype } from "../../util";
import CreateNewVersion from "../CreateNewVersion";
import { VersioningItemView } from "./VersioningItemView";
import { VersioningItemViewListComponent } from "./VersioningItemViewListComponent";
import { VersioningSortingSelector } from "./VersioningSortingSelector";
import { VerticalTimeline } from "react-vertical-timeline-component";

interface StyleProps {
    subtypeSwatch?: Swatch;
}

const useStyles = (props: StyleProps) =>
    makeStyles((theme: Theme) =>
        createStyles({
            root: {
                display: "flex",
                flexDirection: "row",
                width: "100%",
                alignItems: "start",
                justifyContent: "space-between",
            },
            toolBar: {
                width: "100%",
                justifyContent: "space-between",
            },
            icon: {
                fontSize: "25px",
            },
            lhContentList: {
                display: "flex",
                flexDirection: "row",
                width: "100%",
                justifyContent: "start",
                alignItems: "start",
                paddingTop: theme.spacing(2),
            },
            lhTopToolBar: {
                width: "100%",
                justifyContent: "start",
            },
            rhActionButtons: {
                display: "flex",
                flexDirection: "row",
                width: "100%",
                flexWrap: "wrap",
                justifyContent: "end",
                alignItems: "stretch",
            },
            actionButton: {
                paddingLeft: theme.spacing(1),
                paddingBottom: theme.spacing(1),
            },
            // For Create New Version disabled tooltip
            newVersionTooltip: {
                color: theme.palette.common.white,
                "& a:hover": { cursor: "pointer" },
            },
            // Unify the layout with versioningItemViewListComponent's layout
            verticalTimelineContainer: {
                margin: 0,
            },
            // Other general styles
            fullWidth: { width: "100%" },
        })
    );

// Versioning view
export type VersionPrefix =
    | "Original version"
    | "Current version"
    | "Current (Latest) version"
    | "Latest version"
    | "Version";

export interface VersioningItem {
    id: string;
    versionReason?: string;
    ownerUsername: string;
    version?: number;
    createdTimestamp: number;
}

const itemBaseToVersioningItem = (
    item?: ItemBase
): VersioningItem | undefined => {
    const result: VersioningItem | undefined =
        !!item && !!item.versioning_info
            ? {
                  id: item.id,
                  versionReason: item.versioning_info?.reason,
                  ownerUsername: item.owner_username,
                  version: item.versioning_info?.version,
                  createdTimestamp: item.created_timestamp,
              }
            : undefined;
    return result;
};

export interface VersioningItemViewList {
    topVersion?: VersioningItem;
    topExpandVersions: VersioningItem[];
    bottomExpandVersions: VersioningItem[];
    bottomVersion?: VersioningItem;
}

interface GenerateVersioningItemViewListProps {
    itemList: LoadedEntity<ItemBase>[];
    // Current item index
    startingItemIndex: number;
}

interface GenerateVersioningItemViewListOutPuts {
    resolvedList: VersioningItemViewList;
    currentIsOriginal: boolean;
    currentIsLatest: boolean;
}

const generateVersioningItemViewList = (
    props: GenerateVersioningItemViewListProps
): GenerateVersioningItemViewListOutPuts => {
    /* 
    This function helps turn ordered itemList: LoadedEntity<ItemBase> into VersioningItemViewList,  
    (topVersion, topExpandVersions list, bottomVersion and bottomExpandVersions list) 
    and could be directly display for the vertical timeline. 
     **/

    const list: LoadedEntity<ItemBase>[] = props.itemList;

    const listLength = list.length;

    // Will separate top and bottom based on current position/index
    const currentItemIndex = props.startingItemIndex;

    // listLength <= 1

    // If only have current item, don't show either expand icons or the top/bottom versions
    if (listLength <= 1) {
        return {
            resolvedList: {
                topExpandVersions: [],
                bottomExpandVersions: [],
            },
            currentIsOriginal: true,
            currentIsLatest: true,
        };
    }

    // listLength >1

    //Output list, set the first and last value, if there is current version set, will be override to undefined later
    var resultList: VersioningItemViewList = {
        topVersion: itemBaseToVersioningItem(list[0].data),
        topExpandVersions: [],
        bottomExpandVersions: [],
        bottomVersion: itemBaseToVersioningItem(list[listLength - 1].data),
    };

    // Record if current is original version or is latest version or neither
    var currentIsOriginal: boolean = false;

    var currentIsLatest: boolean = false;

    // only for at least 3 items in the list, we need to set the expanded list
    if (listLength > 2) {
        // Set list on the top
        // If currentItemIndex <= 1, [] will  be return
        const topExpandVersions: Array<VersioningItem | undefined> = list
            .slice(1, currentItemIndex)
            .map((item: LoadedEntity<ItemBase>) => {
                return !!item.data
                    ? itemBaseToVersioningItem(item.data)
                    : undefined;
            });

        resultList.topExpandVersions = topExpandVersions.every((item) => !!item)
            ? (topExpandVersions as VersioningItem[])
            : [];
        // Set list on the bottom
        // If listLength - 1 <= currentItemIndex + 1, [] will be return
        const bottomExpandVersions: Array<VersioningItem | undefined> = list
            .slice(currentItemIndex + 1, listLength - 1)
            .map((item: LoadedEntity<ItemBase>) => {
                return !!item.data
                    ? itemBaseToVersioningItem(item.data)
                    : undefined;
            });

        resultList.bottomExpandVersions = bottomExpandVersions.every(
            (item) => !!item
        )
            ? (bottomExpandVersions as VersioningItem[])
            : [];
    }

    // If current version is the top version, set top version to undefined, and won't show the top version later,
    if (props.startingItemIndex === 0) {
        // Current item is original version
        currentIsOriginal = true;

        resultList.topVersion = undefined;
        resultList.topExpandVersions = [];
    }

    // If current version is the bottom version, set bottom version to undefined, and won't show the bottom version later
    if (props.startingItemIndex === listLength - 1) {
        // Current item is the latest version
        currentIsLatest = true;

        resultList.bottomExpandVersions = [];
        resultList.bottomVersion = undefined;
    }

    return { resolvedList: resultList, currentIsOriginal, currentIsLatest };
};

interface VersioningViewProps {
    item: ItemBase;
    isAdmin: boolean;
    // For SubtypeHeaderComponent
    showSubtypeHeaderComponent: boolean;
    isUser?: boolean;
    locked?: boolean;
    lockedContent?: JSX.Element;
    // Path for jumping between item's tabs, used for registry or datastore
    versionIdLinkResolver: (id: string) => string;
}

export const VersioningView = (props: VersioningViewProps) => {
    /**
    Component: VersioningView
    */

    const subtypeSwatch = getSwatchForSubtype(props.item?.item_subtype);

    const classes = useStyles({ subtypeSwatch: subtypeSwatch })();

    const subtypeIcon = assignIcon(props.item.item_subtype, classes.icon);

    const HELP_LINK =
        DOCUMENTATION_BASE_URL + "/versioning/versioning-overview.html";

    // Open create new version dialog
    const [openCreateNewVersion, setOpenCreateNewVersion] =
        useState<boolean>(false);

    // true: old version is at top; false: newest version is at top
    const [ascending, setAscending] = useState<boolean>(false);

    const [topExpand, setTopExpand] = useState<boolean>(false);
    const [bottomExpand, setBottomExpand] = useState<boolean>(false);

    const [versioningItemList, setVersioningItemList] =
        useState<VersioningItemViewList>({
            topExpandVersions: [],
            bottomExpandVersions: [],
        });

    var loading = true;
    var versioningListErrorOccurred = false;

    // Only admin in the lasted version can see the "create new version button"
    const isAdmin = props.isAdmin;
    const isHeadVersion = !!!props.item.versioning_info?.next_version;
    const showCreateNewVersion = isAdmin;

    // Path to latest version's tab
    const history = useHistory();

    // Current Item
    const item: ItemBase = props.item;

    // Check current item versioning info
    if (item.versioning_info === undefined) {
        return (
            <Alert
                variant="outlined"
                severity="error"
                className={classes.fullWidth}
            >
                <AlertTitle>
                    Error: Current entity's versioning information could not be
                    found
                </AlertTitle>
                Error occurred when getting current entity's versioning
                information
            </Alert>
        );
    }

    // Check if current version is initial version, if it is, do not show version note
    const currentVersionNote: string | undefined = !!item.versioning_info
        .previous_version
        ? item.versioning_info.reason
        : undefined;

    // Show the current version first while waiting for the versioning list loading
    const currentVersion: VersioningItem = {
        id: item.id,
        versionReason: currentVersionNote,
        ownerUsername: item.owner_username,
        version: !!item.versioning_info
            ? item.versioning_info.version
            : undefined,
        createdTimestamp: item.created_timestamp,
    };

    // Load full version list
    const loadedVersionList = useLoadedVersionList({ startingItem: item });
    // Ascending
    const ascendingVersionList: LoadedEntity<ItemBase>[] = JSON.parse(
        JSON.stringify(loadedVersionList.items)
    );

    // Descending
    const loadedVersionListCopy: LoadedEntity<ItemBase>[] = JSON.parse(
        JSON.stringify(loadedVersionList.items)
    );
    const descendingVersionList: LoadedEntity<ItemBase>[] = JSON.parse(
        JSON.stringify(loadedVersionListCopy.reverse())
    );
    const descendingStartingIndex: number =
        loadedVersionList.items.length - loadedVersionList.startingIndex - 1;

    // For setting versioning list when version data complete
    useEffect(() => {
        if (loadedVersionList.success && loadedVersionList.complete) {
            const versionsViewList = generateVersioningItemViewList({
                itemList: descendingVersionList,
                startingItemIndex: descendingStartingIndex,
            });
            setVersioningItemList(versionsViewList.resolvedList);
        }
    }, [loadedVersionList.loading]);

    // For tracking sorting changes, and update the versioning list based on ascending or descending
    useEffect(() => {
        // ascending update
        setTopExpand(false);
        setBottomExpand(false);
        // ascending value from last render
        if (ascending) {
            const versionsViewList = generateVersioningItemViewList({
                itemList: ascendingVersionList,
                startingItemIndex: loadedVersionList.startingIndex,
            });
            setVersioningItemList(versionsViewList.resolvedList);
        } else {
            const versionsViewList = generateVersioningItemViewList({
                itemList: descendingVersionList,
                startingItemIndex: descendingStartingIndex,
            });
            setVersioningItemList(versionsViewList.resolvedList);
        }
    }, [ascending]);

    if (
        !!loadedVersionList.items &&
        !loadedVersionList.loading &&
        loadedVersionList.success &&
        loadedVersionList.complete
    ) {
        // All versions completed successfully
        loading = false;
    } else if (loadedVersionList.error) {
        loading = false;
        versioningListErrorOccurred = true;
    } else {
        loading = true;
    }

    // Get path value to item's tab
    const latestVersionId = descendingVersionList[0].data?.id;
    const latestVersionPath: string | undefined = !!latestVersionId
        ? props.versionIdLinkResolver(latestVersionId)
        : undefined;

    // Views

    const createNewVersionTooltipText = (
        <Typography variant="body1" className={classes.newVersionTooltip}>
            You cannot create a new version from an out of date item, click{" "}
            <span>
                <a
                    onClick={() => {
                        if (!!latestVersionId && !!latestVersionPath)
                            history.push(latestVersionPath);
                    }}
                >
                    here
                </a>
            </span>{" "}
            to open the latest version.
        </Typography>
    );

    const versioningListView = versioningListErrorOccurred ? (
        <React.Fragment>
            <Alert
                variant="outlined"
                severity="error"
                className={classes.fullWidth}
            >
                <AlertTitle>
                    Error: Versioning list could not be retrieved
                </AlertTitle>
                Error: {loadedVersionList.errorMessage ?? "Unknown."}
            </Alert>

            {/* Only show current Version Item */}
            <VersioningItemView
                versionPrefix={"Current version"}
                versioningItem={currentVersion}
                subtypeSwatch={subtypeSwatch}
                subtypeIcon={subtypeIcon}
                versionIdLinkResolver={props.versionIdLinkResolver}
            />
        </React.Fragment>
    ) : loading ? (
        <React.Fragment>
            <Stack direction="row" className={classes.fullWidth}>
                <CircularProgress />
                <Typography variant="body1" paddingLeft={2} paddingTop={2}>
                    Loading versions...
                </Typography>
            </Stack>
            <VerticalTimeline
                className={classes.verticalTimelineContainer}
                lineColor={subtypeSwatch.colour}
                animate={false}
                layout="1-column-left"
            >
                <VersioningItemView
                    versionPrefix={"Current version"}
                    versioningItem={currentVersion}
                    subtypeSwatch={subtypeSwatch}
                    subtypeIcon={subtypeIcon}
                    versionIdLinkResolver={props.versionIdLinkResolver}
                />
            </VerticalTimeline>
        </React.Fragment>
    ) : (
        <VersioningItemViewListComponent
            versioningItemList={versioningItemList}
            subtypeSwatch={subtypeSwatch}
            subtypeIcon={subtypeIcon}
            topExpand={topExpand}
            setTopExpand={setTopExpand}
            bottomExpand={bottomExpand}
            setBottomExpand={setBottomExpand}
            ascending={ascending}
            loading={loading}
            currentVersion={currentVersion}
            currentVersionIsLatest={isHeadVersion}
            versionIdLinkResolver={props.versionIdLinkResolver}
        />
    );

    // Handlers

    // Create a new version

    const handleCreateNewVersion = () => {
        setOpenCreateNewVersion(true);
    };

    return (
        <Stack direction="column" spacing={1}>
            {props.showSubtypeHeaderComponent && (
                <SubtypeHeaderComponent
                    item={props.item!}
                    isUser={props.isUser}
                    locked={props.locked}
                    lockedContent={props.lockedContent}
                />
            )}

            <Grid container xs={12} className={classes.root}>
                {/* Sorting and buttons */}
                <Grid container item xs={12} className={classes.toolBar}>
                    {/* Versioning list sorting */}
                    <Grid item xs={4} className={classes.lhTopToolBar}>
                        <VersioningSortingSelector
                            ascending={ascending}
                            setAscending={setAscending}
                            disabled={loading}
                        />
                    </Grid>
                    {/* Action buttons view */}
                    <Grid
                        container
                        item
                        xs={8}
                        className={classes.rhActionButtons}
                    >
                        {showCreateNewVersion && (
                            <Grid item className={classes.actionButton}>
                                {isHeadVersion ? (
                                    <Button
                                        variant="contained"
                                        onClick={handleCreateNewVersion}
                                        disabled={loading}
                                    >
                                        Create New Version
                                    </Button>
                                ) : (
                                    <Tooltip
                                        title={createNewVersionTooltipText}
                                    >
                                        <Box>
                                            <Button
                                                variant="contained"
                                                disabled={true}
                                            >
                                                Create New Version
                                            </Button>
                                        </Box>
                                    </Tooltip>
                                )}
                            </Grid>
                        )}
                        {openCreateNewVersion && (
                            <CreateNewVersion
                                item={props.item!}
                                open={openCreateNewVersion}
                                setOpenInParent={setOpenCreateNewVersion}
                                versionIdLinkResolver={
                                    props.versionIdLinkResolver
                                }
                            />
                        )}
                        <Grid item className={classes.actionButton}>
                            <Button
                                variant="contained"
                                onClick={() => {
                                    window.open(
                                        HELP_LINK,
                                        "_blank",
                                        "noopener,noreferrer"
                                    );
                                }}
                                endIcon={<HelpOutline />}
                            >
                                Help
                            </Button>
                        </Grid>
                    </Grid>
                </Grid>
                {/* Versioning list view */}
                <Grid
                    container
                    item
                    xs={12}
                    className={classes.lhContentList}
                    rowGap={4}
                >
                    <Grid item xs={12}>
                        {versioningListView}
                    </Grid>
                </Grid>
            </Grid>
        </Stack>
    );
};
