import { Menu } from "@mui/icons-material";
import {
    AppBar,
    Button,
    Container,
    Divider,
    Drawer,
    IconButton,
    Stack,
    Toolbar,
    Typography,
} from "@mui/material";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { observer } from "mobx-react-lite";
import { useContext, useEffect, useState } from "react";
import {
    DATA_STORE_LINK,
    PROV_STORE_LINK,
    ProtectedRoute,
    SideNavBox,
} from "react-libs";
import { ProfileIcon } from "react-libs";
import { Footer } from "react-libs/components/Footer";
import { Route, Link as RouterLink, Switch } from "react-router-dom";
import {
    CONTACT_US_BUTTON_LINK,
    DOCUMENTATION_BASE_URL,
    LANDING_PAGE_LINK,
} from "react-libs";
import "../css/Parent.css";
import Frontmatter from "../pages/Frontmatter";
import Item from "../pages/Item";
import Profile from "../pages/Profile";
import Records from "../pages/Records";
import RegisterEntity from "../pages/RegisterEntity";
import { ThemeConfigContext } from "../index";
import { DefaultTheme } from "@mui/styles";

const useStyles = makeStyles((theme: DefaultTheme) =>
    createStyles({
        root: {
            display: "flex",
            backgroundImage: `url(${theme.backgroundImgURL})`,
            backgroundRepeat: "no-repeat",
            backgroundSize: "cover",
            backgroundAttachment: "fixed",
        },
        menuBtn: {
            color: "white",
        },
        button: {
            margin: 20,
        },
        container: {
            marginTop: 100,
            marginBottom: 20,
            minHeight: "60vh",
        },
        appBar: {
            zIndex: theme.zIndex.drawer + 1,
            color: "white",
        },
        routerButtonDefault: {
            color: "white",
            height: 64,
            borderRadius: 0,
            padding: "0px 8px",
            "&:hover": {
                backgroundColor: theme.palette.primary.light,
            },
        },
        routerButtonActive: {
            color: "white",
            height: 64,
            borderRadius: 0,
            padding: "0px 24px",
            borderBottom: "2px solid white",
        },
        margin: {
            margin: theme.spacing(1),
            color: "white",
        },
        extendedIcon: {
            marginRight: theme.spacing(1),
        },
        tab: {
            ...theme.mixins.toolbar,
            color: "white",
            "&.Mui-selected": {
                color: "white",
                backgroundColor: `rgba(255,255,255,0.1)`,
            },
        },
    })
);

function RoutesAndLayout() {
    const classes = useStyles();

    // Pull current theme config
    const themeConfig = useContext(ThemeConfigContext);

    const { keycloak, initialized } = useKeycloak();

    const [open, setOpen] = useState(false);

    const toggleSlider = () => {
        setOpen(!open);
    };

    return (
        <div>
            <Drawer open={open} anchor="left" onClose={toggleSlider}>
                <SideNavBox
                    navListItems={[
                        {
                            listText: "Landing Portal",
                            href: LANDING_PAGE_LINK,
                        },
                        {
                            listText: "Data Store",
                            href: DATA_STORE_LINK,
                        },
                        {
                            listText: "Provenance Store",
                            href: PROV_STORE_LINK,
                        },
                        {
                            listText: "Knowledge Hub",
                            href: DOCUMENTATION_BASE_URL,
                        },
                    ]}
                />
            </Drawer>
            <AppBar position="fixed" className={classes.appBar}>
                <Container>
                    <Toolbar>
                        <Stack
                            direction="row"
                            justifyContent="space-between"
                            alignItems="center"
                            style={{ width: "100%" }}
                            padding={0.5}
                        >
                            <Stack
                                direction="row"
                                alignItems="center"
                                spacing={3}
                            >
                                <IconButton
                                    onClick={toggleSlider}
                                    className={classes.menuBtn}
                                >
                                    <Menu />
                                </IconButton>
                                <RouterLink to="/">
                                    <Typography
                                        variant="h6"
                                        component="div"
                                        className={classes.appBar}
                                    >
                                        {
                                            themeConfig.currentPageThemeConfig
                                                .appBarTitle
                                        }
                                    </Typography>
                                </RouterLink>
                            </Stack>
                            <Stack
                                direction="row"
                                alignItems="center"
                                divider={
                                    <Divider orientation="vertical" flexItem />
                                }
                            >
                                <Button
                                    href="/records"
                                    className={classes.routerButtonDefault}
                                >
                                    Explore Registry
                                </Button>
                                <Button
                                    href={CONTACT_US_BUTTON_LINK}
                                    target="_blank"
                                    className={classes.routerButtonDefault}
                                >
                                    Contact us
                                </Button>
                                <ProfileIcon
                                    isLoggedIn={keycloak.authenticated ?? false}
                                    username={
                                        keycloak.tokenParsed
                                            ? keycloak.tokenParsed.email
                                            : "Unknown"
                                    }
                                />
                            </Stack>
                        </Stack>
                    </Toolbar>
                </Container>
            </AppBar>
            <div className={classes.root}>
                <Container className={classes.container}>
                    <Switch>
                        <Route exact path="/" component={Frontmatter} />
                        <ProtectedRoute path="/registerentity">
                            <RegisterEntity mode="new" />
                        </ProtectedRoute>
                        <ProtectedRoute path="/editentity">
                            <RegisterEntity mode="edit" />
                        </ProtectedRoute>
                        <ProtectedRoute path="/cloneentity">
                            <RegisterEntity mode="clone" />
                        </ProtectedRoute>
                        <ProtectedRoute path="/records">
                            <Records />
                        </ProtectedRoute>
                        <ProtectedRoute path="/item/:idPrefix/:idSuffix">
                            <Item />
                        </ProtectedRoute>
                        <ProtectedRoute path="/profile">
                            <Profile />
                        </ProtectedRoute>
                    </Switch>
                </Container>
            </div>
            <Footer {...themeConfig.footerConfig} />
        </div>
    );
}

export default observer(RoutesAndLayout);
