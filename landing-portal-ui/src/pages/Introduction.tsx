import {
    Alert,
    AlertTitle,
    Button,
    Card,
    CardActions,
    CardContent,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Grid,
    Stack,
    Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { observer } from "mobx-react-lite";
import { useContext } from "react";
import {
    BoundedContainer,
    DOCUMENTATION_BASE_URL,
    useUserLinkServiceLookup
} from "react-libs";
import { LandingPortalThemeConfig } from "react-libs/util/themeValidation";
import { ThemeConfigContext } from "../index";
import accessStore from "../stores/accessStore";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            display: "flex",
            flexWrap: "wrap",
            flexFlow: "column",
            justifyContent: "top",
            alignItems: "center",
            minHeight: "60vh",
            marginTop: 50,
        },
        margin: {
            margin: theme.spacing(1),
            width: 400,
        },
        button: {
            margin: 20,
            marginRight: theme.spacing(1),
        },
        instructions: {
            marginTop: theme.spacing(1),
            marginBottom: theme.spacing(1),
        },
        centerLoading: {
            display: "flex",
            justifyContent: "center",
        },
        paper: {
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
        rowGrid: {
            display: "flex",
            alignItems: "stretch",
        },
        card: {
            display: "flex",
            flexDirection: "column",
            backgroundColor: theme.palette.common.white,
            borderRadius: 5,
            margin: theme.spacing(2),
            float: "left",
            width: "100%",
        },
        cardContent: {
            flexGrow: 1,
        },
        introTopSection: {
            padding: theme.spacing(2),
        },
        description: {
            paddingBottom: 10,
        },
        descriptionTitle: {
            paddingBottom: 50,
        },
        actionButton: {
            marginTop: theme.spacing(3),
            marginBottom: theme.spacing(4),
            marginRight: theme.spacing(1),
        },
    })
);

interface UserLinkCheckDisplayComponentProps {}
const UserLinkCheckDisplayComponent = (
    props: UserLinkCheckDisplayComponentProps
) => {
    /**
    Component: UserLinkCheckDisplayComponent
    
    Displays a banner prompting the user to link their identity.
    */

    const toolLink = "/profile?function=identity";
    const docLink =
        DOCUMENTATION_BASE_URL +
        "/getting-started-is/linking-identity.html";

    const content: JSX.Element = (
        <Stack direction="column" spacing={2}>
            <p>
                To register and manage data, entities and provenance in the
                system, you must to register yourself as a Person in the
                Registry and link yourself to this identity. We have detected
                that your account is not linked to a Person.
            </p>
            <p>
                <a href={toolLink}>Click here</a> to link yourself to a Person
                in the Registry. For more help, visit our{" "}
                <a href={docLink}>documentation</a>.
            </p>
        </Stack>
    );

    return (
        <Alert severity="warning" variant="outlined">
            <AlertTitle>User is not linked to a Registered Person</AlertTitle>
            {content}
        </Alert>
    );
};

interface ActionCardsProps {}
const ActionCards = observer((props: ActionCardsProps) => {
    /**
    Component: ActionCards
    
    */
    const classes = useStyles();

    // Pull theme config
    const themeConfig = useContext(ThemeConfigContext);
    const landingPortalConfig =
        themeConfig.currentPageThemeConfig as LandingPortalThemeConfig;

    //check if card content is undefined, if so, hide the card.
    const emptyLhCard =
        landingPortalConfig.lhCardTitle === undefined &&
        landingPortalConfig.lhCardBodyHtml === undefined &&
        landingPortalConfig.lhCardActionsHtml === undefined;
    const emptyRhCard =
        landingPortalConfig.rhCardTitle === undefined &&
        landingPortalConfig.rhCardBodyHtml === undefined &&
        landingPortalConfig.rhCardActionsHtml === undefined;

    return (
        <Grid container justifyContent="space-between">
            <Grid xs={6} className={classes.rowGrid}>
                {!emptyLhCard && (
                    <Card className={classes.card}>
                        <CardContent className={classes.cardContent}>
                            <Typography
                                gutterBottom
                                variant="h6"
                                component="div"
                            >
                                {landingPortalConfig.lhCardTitle}
                            </Typography>
                            <Typography
                                variant="body1"
                                className={classes.description}
                            >
                                {landingPortalConfig.lhCardBodyHtml}
                            </Typography>
                        </CardContent>
                        <CardActions>
                            <Grid
                                container
                                xs={12}
                                justifyContent={"space-evenly"}
                            >
                                {landingPortalConfig.lhCardActionsHtml}
                            </Grid>
                        </CardActions>
                    </Card>
                )}
            </Grid>
            <Grid xs={6} className={classes.rowGrid}>
                {!emptyRhCard && (
                    <Card className={classes.card}>
                        <CardContent className={classes.cardContent}>
                            <Typography
                                gutterBottom
                                variant="h6"
                                component="div"
                            >
                                {landingPortalConfig.rhCardTitle}
                            </Typography>
                            <Typography
                                variant="body1"
                                className={classes.description}
                            >
                                {landingPortalConfig.rhCardBodyHtml}
                            </Typography>
                        </CardContent>
                        <CardActions>
                            <Grid container justifyContent="space-evenly">
                                {landingPortalConfig.rhCardActionsHtml}
                            </Grid>
                        </CardActions>
                    </Card>
                )}
            </Grid>
        </Grid>
    );
});

const Introduction = observer(() => {
    const classes = useStyles();

    // Pull theme config
    const themeConfig = useContext(ThemeConfigContext);
    const landingPortalConfig =
        themeConfig.currentPageThemeConfig as LandingPortalThemeConfig;

    // This is used to check if banner should be displayed
    const shouldLink = useUserLinkServiceLookup({}).shouldLink;

    const newUserDialog = (
        <Dialog
            open={accessStore.accessRoleIsEmpty}
            onClose={() => accessStore.closeFirstTimeLoginAlert()}
        >
            <DialogTitle>New User Notice</DialogTitle>
            <DialogContent>
                We have detected that you have no roles attached to your
                account. You can use the profile icon button in the top right of
                the screen to visit your profile. Then click the Roles tab to
                view and request additional roles. For more information about
                how to request access permissions for the system please visit{" "}
                <a
                    href={
                        DOCUMENTATION_BASE_URL +
                        "/getting-started-is/requesting-access-is.html"
                    }
                    target="_blank"
                >
                    {" "}
                    our guide
                </a>
                .
            </DialogContent>
            <DialogActions>
                <Button onClick={() => accessStore.closeFirstTimeLoginAlert()}>
                    Confirm
                </Button>
            </DialogActions>
        </Dialog>
    );

    return (
        <div className={classes.root}>
            <BoundedContainer breakpointKey={"lg"}>
                {newUserDialog}
                <Grid className={classes.paper} spacing={2}>
                    {shouldLink && (
                        <Grid item xs={12} className={classes.introTopSection}>
                            <UserLinkCheckDisplayComponent />
                        </Grid>
                    )}
                    <Grid container xs={12}>
                        <Grid xs={6} className={classes.introTopSection}>
                            <Typography
                                variant="h5"
                                className={classes.descriptionTitle}
                            >
                                {landingPortalConfig.introductionTitle}
                            </Typography>

                            <Typography
                                gutterBottom
                                variant="h6"
                                component="div"
                            >
                                Getting Started
                            </Typography>
                            <Typography variant="body1" color="text.secondary">
                                {landingPortalConfig.introductionBodyHtml}
                            </Typography>
                            <Grid
                                container
                                justifyContent="space-evenly"
                                alignContent="center"
                            >
                                <Button
                                    className={classes.actionButton}
                                    variant="outlined"
                                    href={
                                        DOCUMENTATION_BASE_URL +
                                        "/getting-started-is/logging-in.html"
                                    }
                                    target="_blank"
                                >
                                    Logging in
                                </Button>
                                <Button
                                    className={classes.actionButton}
                                    variant="outlined"
                                    href={
                                        DOCUMENTATION_BASE_URL +
                                        "/getting-started-is/requesting-access-is.html"
                                    }
                                    target="_blank"
                                >
                                    How to request access
                                </Button>
                            </Grid>
                        </Grid>
                        <Grid xs={6}>
                            <div className={classes.description}>
                                <img
                                    src="/provena_components.png"
                                    width="100%"
                                />
                            </div>
                        </Grid>
                    </Grid>
                    <Grid item xs={12} className={classes.paper}>
                        <ActionCards />
                    </Grid>
                </Grid>
            </BoundedContainer>
        </div>
    );
});
export default Introduction;
