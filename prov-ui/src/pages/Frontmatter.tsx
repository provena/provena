import { Button, Grid, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { observer } from "mobx-react-lite";
import {
    BoundedContainer,
    DOCUMENTATION_BASE_URL,
    REGISTRY_LINK,
} from "react-libs";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            display: "flex",
            flexWrap: "wrap",
            flexFlow: "column",
            justifyContent: "center",
            alignItems: "center",
        },
        button: {
            marginRight: theme.spacing(4),
        },
        paper: {
            padding: theme.spacing(4),
            borderRadius: 5,
            backgroundColor: theme.palette.common.white,
            width: "100%",
            marginTop: theme.spacing(2),
            marginBottom: theme.spacing(4),
        },
        card: {
            backgroundColor: theme.palette.common.white,
            borderRadius: 5,
            margin: theme.spacing(2),
            float: "left",
        },
        padding: {
            padding: theme.spacing(2),
        },
        actionButton: {
            marginTop: theme.spacing(3),
            marginBottom: theme.spacing(4),
            marginRight: theme.spacing(1),
        },
        linkListItem: {
            marginTop: 10,
            "&:hover": {
                background: "#C3ccd0",
            },
            minHeight: 30,
        },
    })
);

const Frontmatter = observer(() => {
    const classes = useStyles();
    return (
        <div className={classes.root}>
            <BoundedContainer breakpointKey={"lg"}>
                <Grid className={classes.paper}>
                    <Grid container>
                        <Grid item xs={9} className={classes.padding}>
                            <Typography variant="h5">
                                Register and explore modelling and data
                                provenance
                            </Typography>
                            <br />
                            <img src="/provenance-graph.png" width="80%" />
                            <Typography variant="body1">
                                The Provenance Store and associated tools enable
                                the registration of workflow provenance into an
                                interconnected graph of registered items.
                                Capturing the provenance of activities
                                significantly enhances the transparency of
                                scientific workflows. The exploration, querying
                                and referencing of provenance facilitates
                                reproducibility and trust in the process's
                                outputs.
                            </Typography>
                            <br />
                            <Typography variant="body1">
                                Get started by registering provenance with our
                                tools or by exploring items and their lineage in
                                the Entity Registry.
                            </Typography>
                            <br />
                            <div>
                                <Grid container justifyContent="space-evenly">
                                    <Button
                                        className={classes.actionButton}
                                        variant="outlined"
                                        href="/tools"
                                    >
                                        Provenance registration tools
                                    </Button>
                                    <Button
                                        className={classes.actionButton}
                                        variant="outlined"
                                        href={REGISTRY_LINK}
                                    >
                                        Explore registered entities
                                    </Button>
                                </Grid>
                            </div>
                        </Grid>
                        <Grid item xs={3}>
                            <Typography variant="h6">Find out more</Typography>
                            <Typography
                                variant="body1"
                                className={classes.linkListItem}
                            >
                                <a target="doc" href={DOCUMENTATION_BASE_URL}>
                                    Learn more about Provena
                                </a>
                            </Typography>
                            <Typography
                                variant="body1"
                                className={classes.linkListItem}
                            >
                                <a
                                    target="doc"
                                    href={
                                        DOCUMENTATION_BASE_URL +
                                        "/provenance/overview/what-is-provenance.html"
                                    }
                                >
                                    Learn more about provenance
                                </a>
                            </Typography>
                            <Typography
                                variant="body1"
                                className={classes.linkListItem}
                            >
                                <a
                                    target="doc"
                                    href={
                                        DOCUMENTATION_BASE_URL +
                                        "/provenance/registering-model-runs/"
                                    }
                                >
                                    How do I register provenance?
                                </a>
                            </Typography>
                            <Typography
                                variant="body1"
                                className={classes.linkListItem}
                            >
                                <a
                                    target="doc"
                                    href={
                                        DOCUMENTATION_BASE_URL +
                                        "/provenance/exploring-provenance/"
                                    }
                                >
                                    How do I explore provenance?
                                </a>
                            </Typography>
                        </Grid>
                    </Grid>
                </Grid>
            </BoundedContainer>
        </div>
    );
});

export default Frontmatter;
