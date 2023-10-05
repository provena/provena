import { Button, Grid, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { observer } from "mobx-react-lite";
import { BoundedContainer, DOCUMENTATION_BASE_URL } from "react-libs";
import "../css/Parent.css";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            display: "flex",
            flexWrap: "wrap",
            flexFlow: "column",
            justifyContent: "center",
            alignItems: "center",
        },
        topPanel: {
            padding: theme.spacing(4),
            borderRadius: 5,
            backgroundColor: theme.palette.common.white,
            width: "100%",
            marginTop: theme.spacing(2),
            marginBottom: theme.spacing(4),
            alignItems: "center",
            justifyContent: "space-between",
        },
        actionContainer: {
            display: "flex",
            justifyContent: "space-between",
            flexDirection: "row",
            marginBottom: theme.spacing(4),
        },
        optionPanel: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexDirection: "column",
            backgroundColor: theme.palette.common.white,
            borderRadius: 5,
            padding: theme.spacing(2),
        },
        actionButton: {
            marginTop: theme.spacing(3),
            marginBottom: theme.spacing(4),
        },
        padding: {
            padding: theme.spacing(2),
        },
    })
);

const Frontmatter = observer(() => {
    const classes = useStyles();
    return (
        <div className={classes.root}>
            <BoundedContainer breakpointKey={"lg"}>
                <Grid container rowGap={2} className={classes.topPanel}>
                    <Grid item xs={9}>
                        <Typography variant="h5" textAlign="center">
                            Explore and register entities to support modelling
                            and data provenance.
                        </Typography>
                    </Grid>
                    <Grid item xs={3} pl={2}>
                        <Typography variant="h6">Find out more</Typography>
                        <Typography variant="body1">
                            <a target="doc" href={DOCUMENTATION_BASE_URL}>
                                Learn more about Provena
                            </a>
                        </Typography>
                        <Typography variant="body1">
                            <a
                                target="doc"
                                href={
                                    DOCUMENTATION_BASE_URL +
                                    "/registry/overview.html"
                                }
                            >
                                About the Entity Registry
                            </a>
                        </Typography>
                        <Typography variant="body1">
                            <a
                                target="doc"
                                href={
                                    DOCUMENTATION_BASE_URL +
                                    "/registry/registering_and_updating.html"
                                }
                            >
                                How do I register entities?
                            </a>
                        </Typography>
                    </Grid>
                </Grid>
                <Grid container xs={12} className={classes.actionContainer}>
                    <Grid container item xs={6}>
                        <Grid
                            container
                            item
                            sx={{ mr: 2 }}
                            className={classes.optionPanel}
                        >
                            <Typography
                                gutterBottom
                                variant="h5"
                                sx={{ mt: 2 }}
                                textAlign="center"
                            >
                                View, Search, and Explore Entity Records
                            </Typography>
                            <Button
                                className={classes.actionButton}
                                variant="outlined"
                                href="/records"
                            >
                                Explore Records
                            </Button>
                        </Grid>
                    </Grid>
                    <Grid container item xs={6}>
                        <Grid
                            container
                            item
                            sx={{ ml: 2 }}
                            className={classes.optionPanel}
                        >
                            <Typography
                                gutterBottom
                                variant="h5"
                                sx={{ mt: 2 }}
                                textAlign="center"
                            >
                                Register an Entity
                            </Typography>
                            <Button
                                className={classes.actionButton}
                                variant="outlined"
                                href="/registerentity"
                            >
                                Register a new Entity
                            </Button>
                        </Grid>
                    </Grid>
                </Grid>
            </BoundedContainer>
        </div>
    );
});

export default Frontmatter;
