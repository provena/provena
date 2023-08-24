import { Theme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { VerticalTimeline } from "react-vertical-timeline-component";
import { Swatch } from "../../util";
import { VersioningExpandIcon } from "./VersioningExpandIcon";
import { VersioningItemView } from "./VersioningItemView";
import { VersioningItem, VersioningItemViewList } from "./VersioningView";

interface StyleProps {
    subtypeSwatch?: Swatch;
}

const useStyles = (props: StyleProps) =>
    makeStyles((theme: Theme) =>
        createStyles({
            verticalTimelineContainer: {
                margin: 0,
            },
        })
    );

interface VersioningItemViewListComponentProps {
    // Get the list in VersioningItemViewList format
    versioningItemList: VersioningItemViewList;
    // Styles for current subtype
    subtypeSwatch: Swatch;
    subtypeIcon: JSX.Element | null;
    // Handle the list expand functions
    topExpand: boolean;
    setTopExpand: (topExpand: boolean) => void;
    bottomExpand: boolean;
    setBottomExpand: (bottomExpand: boolean) => void;
    // ascending true for original version first, false for latest version first
    ascending: boolean;
    // If parent's data is loading, disable expand function
    loading: boolean;
    // Current version's info
    currentVersion: VersioningItem;
    currentVersionIsLatest: boolean;
    // Path for jumping between item's tabs, used for registry or datastore
    versionIdLinkResolver: (id: string) => string;
}

export const VersioningItemViewListComponent = (
    props: VersioningItemViewListComponentProps
): JSX.Element => {
    /**
    Component: VersioningItemViewListComponent

    Show the whole versioning timeline list based on VersioningItemViewList format
    */

    const classes = useStyles({ subtypeSwatch: props.subtypeSwatch })();

    return (
        <VerticalTimeline
            className={classes.verticalTimelineContainer}
            lineColor={props.subtypeSwatch.colour}
            animate={true}
            layout="1-column-left"
        >
            {/* First item */}
            {props.versioningItemList.topVersion !== undefined && (
                <VersioningItemView
                    key={props.versioningItemList.topVersion.id}
                    versionPrefix={
                        props.ascending ? "Original version" : "Latest version"
                    }
                    versioningItem={props.versioningItemList.topVersion}
                    subtypeSwatch={props.subtypeSwatch}
                    subtypeIcon={props.subtypeIcon}
                    versionIdLinkResolver={props.versionIdLinkResolver}
                />
            )}
            {/* Expand Icon for top list */}
            {props.versioningItemList.topExpandVersions.length !== 0 && (
                <VersioningExpandIcon
                    subtypeSwatch={props.subtypeSwatch}
                    subtypeIcon={props.subtypeIcon}
                    expand={props.topExpand}
                    setExpand={props.setTopExpand}
                    loading={props.loading}
                />
            )}
            {/* Top list */}
            {props.topExpand &&
                props.versioningItemList.topExpandVersions.length !== 0 &&
                props.versioningItemList.topExpandVersions.map((item) => (
                    <VersioningItemView
                        key={item.id}
                        versionPrefix={"Version"}
                        versioningItem={item}
                        subtypeSwatch={props.subtypeSwatch}
                        subtypeIcon={props.subtypeIcon}
                        versionIdLinkResolver={props.versionIdLinkResolver}
                    />
                ))}
            {/* Current Version Item */}
            <VersioningItemView
                versionPrefix={
                    props.currentVersionIsLatest
                        ? "Current (Latest) version"
                        : "Current version"
                }
                versioningItem={props.currentVersion}
                subtypeSwatch={props.subtypeSwatch}
                subtypeIcon={props.subtypeIcon}
                versionIdLinkResolver={props.versionIdLinkResolver}
            />
            {/* Bottom list */}
            {props.bottomExpand &&
                props.versioningItemList.bottomExpandVersions.length !== 0 &&
                props.versioningItemList.bottomExpandVersions.map((item) => (
                    <VersioningItemView
                        key={item.id}
                        versionPrefix={"Version"}
                        versioningItem={item}
                        subtypeSwatch={props.subtypeSwatch}
                        subtypeIcon={props.subtypeIcon}
                        versionIdLinkResolver={props.versionIdLinkResolver}
                    />
                ))}
            {/* Expand Icon for bottom list */}
            {props.versioningItemList.bottomExpandVersions.length !== 0 && (
                <VersioningExpandIcon
                    subtypeSwatch={props.subtypeSwatch}
                    subtypeIcon={props.subtypeIcon}
                    expand={props.bottomExpand}
                    setExpand={props.setBottomExpand}
                    loading={props.loading}
                />
            )}
            {/* Last item */}
            {props.versioningItemList.bottomVersion !== undefined && (
                <VersioningItemView
                    key={props.versioningItemList.bottomVersion.id}
                    versionPrefix={
                        props.ascending ? "Latest version" : "Original version"
                    }
                    versioningItem={props.versioningItemList.bottomVersion}
                    subtypeSwatch={props.subtypeSwatch}
                    subtypeIcon={props.subtypeIcon}
                    versionIdLinkResolver={props.versionIdLinkResolver}
                />
            )}
        </VerticalTimeline>
    );
};
