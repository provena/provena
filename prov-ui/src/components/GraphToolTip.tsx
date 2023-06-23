import {
    Alert,
    CircularProgress,
    Grid,
    Stack,
    Typography,
} from "@mui/material";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";
import { HoverData } from "../hooks/useProvGraphData";
import { mapSubTypeToPrettyName } from "react-libs";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        tooltip: {
            position: "absolute",
            left: theme.spacing(1),
            top: theme.spacing(1),
            width: "250px",
            backgroundColor: "rgba(255, 255, 255, 0.95)",
            boxShadow: "rgba(99, 99, 99, 0.2) 0px 2px 8px 0px",
            padding: "10px 10px 20px 10px",
            borderRadius: "5px",
            border: "1px dotted " + theme.palette.primary.dark,
        },
        closeButton: {
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: theme.spacing(1),
        },
        itemPropertyName: {
            fontWeight: theme.typography.fontWeightBold,
        },
        tooltipButton: {
            marginLeft: theme.spacing(1),
            marginRight: theme.spacing(1),
        },
    })
);

export interface GraphToolTipProps {
    hoverData: HoverData;
}
export const GraphToolTip = (props: GraphToolTipProps) => {
    /**
    Component: GraphToolTip
    
    */

    const classes = useStyles();
    return (
        <div
            className={classes.tooltip}
            key={props.hoverData.item?.id ?? "tooltip"}
        >
            {props.hoverData.loading ? (
                <Stack justifyContent="center" alignItems="center">
                    <CircularProgress />
                </Stack>
            ) : props.hoverData.error || !props.hoverData.item ? (
                // Error state
                <Stack justifyContent="center">
                    <Alert variant="outlined" color="error" severity="error">
                        <b>
                            An error occurred while fetching the details for{" "}
                            {props.hoverData.id}
                        </b>
                        <br />
                        Error:{" "}
                        {props.hoverData?.errorMessage ?? "Unknown error."}
                    </Alert>
                </Stack>
            ) : (
                // Main render state
                <Grid>
                    <Grid container>
                        <Grid item xs={4}>
                            <Typography
                                variant="caption"
                                className={classes.itemPropertyName}
                            >
                                ID
                            </Typography>
                        </Grid>

                        <Grid item xs={8}>
                            <Typography variant="caption">
                                {props.hoverData.item.id}
                            </Typography>
                        </Grid>
                    </Grid>
                    {props.hoverData.item.display_name ? (
                        <Grid container>
                            <Grid item xs={4}>
                                <Typography
                                    variant="caption"
                                    className={classes.itemPropertyName}
                                >
                                    NAME
                                </Typography>
                            </Grid>

                            <Grid item xs={8}>
                                <Typography variant="caption">
                                    {props.hoverData.item.display_name}
                                </Typography>
                            </Grid>
                        </Grid>
                    ) : null}
                    {props.hoverData.item.item_subtype ? (
                        <Grid container>
                            <Grid item xs={4}>
                                <Typography
                                    variant="caption"
                                    className={classes.itemPropertyName}
                                >
                                    TYPE
                                </Typography>
                            </Grid>

                            <Grid item xs={8}>
                                <Typography variant="caption">
                                    {mapSubTypeToPrettyName(
                                        props.hoverData.item.item_subtype
                                    )}
                                </Typography>
                            </Grid>
                        </Grid>
                    ) : null}
                </Grid>
            )}
        </div>
    );
};
