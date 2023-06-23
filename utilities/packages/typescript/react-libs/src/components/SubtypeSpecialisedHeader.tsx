import { Box, Divider, Grid, Theme, Typography } from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { ItemBase } from "../shared-interfaces/RegistryModels";
import { assignIcon, getSwatchForSubtype, mapSubTypeToPrettyName } from "../util/subtypeStyling";

interface StyleParams {
    color: string;
    compact: boolean;
}
const useStyles = (props: StyleParams) =>
    makeStyles((theme: Theme) =>
        createStyles({
            bodyPanelContainer: {
                margin: theme.spacing(0),
                width: "100%",
            },
            icon: {
                color: theme.palette.common.white,
                fontSize: props.compact ? "25px" : "30px",
            },
            itemHeaderContainer: {
                marginBottom: theme.spacing(2),
            },
            iconContainer: {
                display: "flex",
                justifyContent: "start",
            },
            iconBackground: {
                display: "flex",
                alignSelf: "end",
                alignItems: "center",
                justifyContent: "space-around",
                backgroundColor: props.color,
                borderRadius: "20px",
                height: props.compact ? "35px" : "40px",
                width: props.compact ? "35px" : "40px",
            },
            headerDivider: {
                borderColor: props.color,
                border: "1px solid",
                width: "100%",
                marginBottom: theme.spacing(3),
            },
        })
    );

interface SubtypeHeaderComponentProps {
    item: ItemBase;
    compact?: boolean;
    isUser?: boolean;
    locked?: boolean;
    lockedContent?: JSX.Element;
}
export const SubtypeHeaderComponent = (props: SubtypeHeaderComponentProps) => {
    /**
    Component: SubtypeHeaderComponent
    
    */

    // determine swatch colour
    const baseSwatch = getSwatchForSubtype(props.item.item_subtype);
    const compact = props.compact ?? false;

    // Use to infill color in styles
    const classes = useStyles({
        color: baseSwatch.colour,
        compact: compact,
    })();

    // Get the correct icon
    let iconSelection = assignIcon(props.item.item_subtype, classes.icon);

    return (
        <Grid container item xs={12} className={classes.bodyPanelContainer}>
            <Grid
                container
                justifyContent={"space-between"}
                className={classes.itemHeaderContainer}
            >
                <Grid item>
                    <Grid container spacing={2}>
                        <Grid item>
                            <Typography
                                variant={compact ? "h5" : "h4"}
                                lineHeight={1}
                                id={"loaded-subtype-title"}
                            >
                                {mapSubTypeToPrettyName(
                                    props.item.item_subtype
                                )}
                                {(props.isUser ?? false) && " (You)"}
                            </Typography>
                        </Grid>
                        {(props.locked ?? false) && (
                            <Grid item>
                                {props.lockedContent ?? (
                                    <p>This item is locked</p>
                                )}
                            </Grid>
                        )}
                    </Grid>
                </Grid>
                <Grid item className={classes.iconContainer}>
                    <Box className={classes.iconBackground}>
                        {iconSelection}
                    </Box>
                </Grid>
            </Grid>

            <Grid item xs={12}>
                <Divider
                    variant="fullWidth"
                    className={classes.headerDivider}
                />
            </Grid>
        </Grid>
    );
};
