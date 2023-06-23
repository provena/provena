import { Button, Grid, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { ThemeConfigContext } from "index";
import { observer } from "mobx-react-lite";
import { useContext, useState } from "react";
import { BoundedContainer, DOCUMENTATION_BASE_URL } from "react-libs";
import { DataStoreThemeConfig } from "react-libs/util/themeValidation";
import { DatasetSearchLinked } from "../components/DatasetSearchBox";

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
        padding: {
            padding: theme.spacing(2),
        },
        actionButton: {
            marginTop: theme.spacing(3),
            marginBottom: theme.spacing(4),
        },
        searchPaper: {
            padding: theme.spacing(2),
            borderRadius: 5,
            backgroundColor: theme.palette.common.white,
            width: "100%",
            marginBottom: theme.spacing(1),
        },
        introduction: {
            minHeight: "50vh",
            marginTop: theme.spacing(4),
            width: "100%",
            display: "flex",
            flexDirection: "column",
        },
    })
);

const Frontmatter = observer(() => {
    const classes = useStyles();

    // Pull theme config
    const themeConfig = useContext(ThemeConfigContext);
    const dataStoreConfig =
        themeConfig.currentPageThemeConfig as DataStoreThemeConfig;

    // Search query
    const [searchQuery, setSearchQuery] = useState<string>("");

    return (
        <div className={classes.root}>
            <BoundedContainer breakpointKey={"lg"}>
                <Grid container rowGap={2} className={classes.topPanel}>
                    <Grid item xs={9}>
                        <Typography variant="h5" textAlign="center">
                            {dataStoreConfig.frontMatterTextHtml}
                        </Typography>
                    </Grid>
                    <Grid item xs={3} pl={2}>
                        <Typography variant="h6">Find out more</Typography>
                        <Typography variant="body1">
                            <a
                                target="doc"
                                href={
                                    DOCUMENTATION_BASE_URL +
                                    "/#what-is-mds-and-its-role"
                                }
                            >
                                Learn more about Provena
                            </a>
                        </Typography>
                        <Typography variant="body1">
                            <a
                                target="doc"
                                href={
                                    DOCUMENTATION_BASE_URL +
                                    "/information-system/data-store/registering-a-dataset.html"
                                }
                            >
                                How do I register data?
                            </a>
                        </Typography>
                    </Grid>
                    <Grid item xs={12}>
                        <DatasetSearchLinked
                            query={searchQuery}
                            setQuery={setSearchQuery}
                            needClearIcon={false}
                        />
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
                                View and explore datasets
                            </Typography>
                            <Button
                                className={classes.actionButton}
                                variant="outlined"
                                href="/datasets"
                            >
                                Explore Datasets
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
                                Register a new dataset
                            </Typography>
                            <Button
                                className={classes.actionButton}
                                variant="outlined"
                                href="/new_dataset"
                            >
                                Register dataset
                            </Button>
                        </Grid>
                    </Grid>
                </Grid>
            </BoundedContainer>
        </div>
    );
});

export default Frontmatter;
