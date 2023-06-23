import { Box, Card, CardContent, Grid, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import {
    CopyFloatingButton,
    assignIcon,
    getSwatchForSubtype,
    mapSubTypeToPrettyName,
    timestampToLocalTime,
} from "react-libs";
import { useHistory } from "react-router-dom";
import { EntityBase } from "../shared-interfaces/RegistryModels";

interface ResultCardProps {
    cardDetails: EntityBase;
    isUser: boolean;
}

const useStyles = (props: any) =>
    makeStyles((theme: Theme) =>
        createStyles({
            resultCardContainer: {
                padding: theme.spacing(1),
            },
            resultCard: {
                display: "flex",
                flexDirection: "row",
                alignContent: "stretch",
                width: "100%",
                backgroundColor: theme.palette.background.paper,
                padding: theme.spacing(1),
                borderRadius: "8px",
                border: "2px solid " + props.swatch.colour,
                "&:hover": {
                    backgroundColor: theme.palette.grey[100],
                    cursor: "pointer",
                },
                minHeight: "350px",
                maxHeight: "380px",
            },
            cardContentContainer: {
                width: "100%",
                display: "flex",
                justifyContent: "space-around",
            },
            cardContent: {
                display: "flex",
                flexDirection: "column",
            },
            cardColourBar: {
                height: "100%",
                minWidth: "20px",
                borderRadius: "8px 0 0 8px",
                backgroundColor: props.swatch.colour,
            },
            cardAction: {
                display: "block",
                textAlign: "initial",
            },
            cardHeader: {
                marginTop: theme.spacing(0),
                marginBottom: theme.spacing(1),
                fontWeight: "bolder",
                overflowwrap: "break-word",
            },
            cardDetailContainer: {
                display: "flex",
                justifyContent: "space-around",
                justifyItems: "stretch",
            },
            cardDetailText: {
                marginBottom: theme.spacing(1),
            },
            cardFooterContainer: {
                width: "100%",
            },
            cardIconContainer: {
                display: "flex",
                justifyContent: "end",
            },
            cardIconBackground: {
                display: "flex",
                alignSelf: "end",
                alignItems: "center",
                justifyContent: "space-around",
                backgroundColor: props.swatch.colour,
                borderRadius: "20px",
                height: "40px",
                width: "40px",
            },
            cardIcon: {
                color: theme.palette.common.white,
                fontSize: "30px",
            },
        })
    );

const truncate = (text: string, length: number = 40) => {
    return text.length > length ? text.substring(0, length - 3) + "..." : text;
};

const ResultCard = (props: ResultCardProps) => {
    const baseSwatch = getSwatchForSubtype(props.cardDetails.item_subtype);
    const classes = useStyles({ swatch: baseSwatch })();
    const history = useHistory();

    let iconSelection = assignIcon(
        props.cardDetails.item_subtype,
        classes.cardIcon
    );
    return (
        <Grid container item xs={3} className={classes.resultCardContainer}>
            <Card
                variant="outlined"
                className={classes.resultCard}
                onClick={() => {
                    history.push(`/item/${props.cardDetails.id}`);
                }}
            >
                <Grid
                    container
                    item
                    xs={1}
                    className={classes.cardColourBar}
                ></Grid>

                <Grid container className={classes.cardContentContainer}>
                    <Grid
                        container
                        item
                        xs={11}
                        className={classes.cardDetailContainer}
                    >
                        <CardContent
                            className={classes.cardContent}
                            style={{ width: "100%" }}
                        >
                            <Typography className={classes.cardHeader}>
                                {mapSubTypeToPrettyName(
                                    props.cardDetails.item_subtype
                                )}
                                {props.isUser && " (You)"}
                            </Typography>
                            <Grid
                                className={classes.cardDetailText}
                                title={props.cardDetails.display_name}
                            >
                                <Typography
                                    variant="body2"
                                    fontWeight={"bold"}
                                    display="inline"
                                >
                                    Name:
                                </Typography>{" "}
                                <span style={{ overflowWrap: "break-word" }}>
                                    {truncate(props.cardDetails.display_name)}
                                </span>
                            </Grid>
                            <Grid className={classes.cardDetailText}>
                                <Typography
                                    variant="body2"
                                    fontWeight={"bold"}
                                    display="inline"
                                >
                                    ID:
                                </Typography>{" "}
                                <Grid container direction="row">
                                    {props.cardDetails.id}
                                    <CopyFloatingButton
                                        clipboardText={props.cardDetails.id}
                                        iconOnly={true}
                                    />
                                </Grid>
                            </Grid>
                            <Grid className={classes.cardDetailText}>
                                <Typography
                                    variant="body2"
                                    fontWeight={"bold"}
                                    display="inline"
                                >
                                    Date Created:
                                </Typography>{" "}
                                {timestampToLocalTime(
                                    props.cardDetails.created_timestamp
                                )}
                            </Grid>
                            <Grid
                                container
                                item
                                xs={12}
                                className={classes.cardFooterContainer}
                            >
                                <Grid
                                    container
                                    item
                                    xs={12}
                                    className={classes.cardIconContainer}
                                >
                                    <Box className={classes.cardIconBackground}>
                                        {iconSelection}
                                    </Box>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Grid>
                </Grid>
            </Card>
        </Grid>
    );
};

export default ResultCard;
