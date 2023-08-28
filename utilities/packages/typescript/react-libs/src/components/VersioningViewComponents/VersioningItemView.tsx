import { Grid, Theme, Typography, useTheme } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { VerticalTimelineElement } from "react-vertical-timeline-component";
import { Swatch, timestampToLocalTime } from "../../util";
import { GenericDetailViewWrapperComponent } from "../JsonRenderer";
import { VersionPrefix, VersioningItem } from "./VersioningView";
import { useHistory } from "react-router-dom";
import { CopyFloatingButton } from "../CopyFloatingButton";
import React from "react";

interface StyleProps {
    subtypeSwatch?: Swatch;
}

const useStyles = (props: StyleProps) =>
    makeStyles((theme: Theme) =>
        createStyles({
            itemViewContainer: {
                display: "flex",
                flexDirection: "column",
                width: "100%",
                borderRadius: "8px",
                padding: theme.spacing(2),
                // Override default timeline element margin top
                "& p": {
                    marginTop: `${theme.spacing(1)} !important`,
                },
            },
            itemViewRow: {
                display: "flex",
                flexDirection: "row",
                justifyContent: "start",
                alignItems: "start",
                width: "100%",
            },
            hoverPointer: {
                "&:hover": {
                    cursor: "pointer",
                },
            },
        })
    );

interface VersioningItemViewProps {
    versionPrefix: VersionPrefix;
    versioningItem: VersioningItem;
    subtypeSwatch: Swatch;
    subtypeIcon: JSX.Element | null;
    // Path for jumping between item's tabs, used for registry or datastore
    versionIdLinkResolver: (id: string) => string;
}

export const VersioningItemView = (props: VersioningItemViewProps) => {
    /**
    Component: VersioningItemView

    Show each item's information with the same layout in a general box
    */

    const classes = useStyles({ subtypeSwatch: props.subtypeSwatch })();
    const theme = useTheme();

    const timeStamp = timestampToLocalTime(
        props.versioningItem.createdTimestamp
    );

    // For highlighting current version
    const iconBackgroundColour =
        props.versionPrefix === ("Current version" as VersionPrefix) ||
        props.versionPrefix === ("Current (Latest) version" as VersionPrefix)
            ? props.subtypeSwatch.tintColour
            : props.subtypeSwatch.colour;

    const iconColour =
        props.versionPrefix === ("Current version" as VersionPrefix) ||
        props.versionPrefix === ("Current (Latest) version" as VersionPrefix)
            ? props.subtypeSwatch.shadeColour
            : theme.palette.common.white;

    const borderStyle: string =
        props.versionPrefix === ("Current version" as VersionPrefix) ||
        props.versionPrefix === ("Current (Latest) version" as VersionPrefix)
            ? `3px solid ${props.subtypeSwatch.colour}`
            : `1px dotted ${props.subtypeSwatch.colour}`;

    // Item details for rendering in timeline element
    const itemDetails: {
        [k: string]: string | JSX.Element | undefined | number;
    } = {
        Id: (
            <React.Fragment>
                <a
                    onClick={() => {
                        history.push(versioningItemTabPath);
                    }}
                    className={classes.hoverPointer}
                >
                    {props.versioningItem.id}
                </a>
                <CopyFloatingButton
                    clipboardText={props.versioningItem.id}
                    iconOnly={true}
                    withConfirmationText={true}
                />
            </React.Fragment>
        ),
        "Version reason": props.versioningItem.versionReason,
        "User name": props.versioningItem.ownerUsername,
        // owner_username: props.versioningItem.ownerUsername,
        Version: props.versioningItem.version ?? "No version number provided.",
    };

    // Link to go to item's versioning tab, used for both both datastore and registry
    const history = useHistory();
    // Set the path for current versioning item
    const versioningItemTabPath = props.versionIdLinkResolver(
        props.versioningItem.id
    );

    return (
        <VerticalTimelineElement
            contentStyle={{
                color: `${props.subtypeSwatch.colour}`,
                boxShadow: "0 0",
            }}
            contentArrowStyle={{ borderRight: "0px solid" }}
            date={timeStamp}
            iconStyle={{
                background: `${iconBackgroundColour}`,
                color: `${iconColour}`,
            }}
            icon={props.subtypeIcon}
        >
            <Grid
                container
                className={classes.itemViewContainer}
                sx={{ border: `${borderStyle}` }}
                rowGap={2}
            >
                <Grid container item xs={12} className={classes.itemViewRow}>
                    <Grid item xs={12}>
                        <Typography
                            variant="body1"
                            color={props.subtypeSwatch.colour}
                            m={0}
                        >
                            <strong>{props.versionPrefix}: </strong>
                        </Typography>
                    </Grid>
                </Grid>
                {Object.entries(itemDetails).map(
                    ([key, val]) =>
                        !(
                            key === "Version reason" &&
                            props.versionPrefix ===
                                ("Original version" as VersionPrefix)
                        ) && (
                            <Grid
                                container
                                item
                                xs={12}
                                className={classes.itemViewRow}
                            >
                                <Grid item xs={4}>
                                    <Typography variant="body1">
                                        {key}
                                    </Typography>
                                </Grid>
                                <Grid item xs={8}>
                                    <Typography variant="body1">
                                        {val}
                                    </Typography>
                                </Grid>
                            </Grid>
                        )
                )}
            </Grid>
        </VerticalTimelineElement>
    );
};
