import Menu from "@mui/icons-material/Menu";
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
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { observer } from "mobx-react-lite";
import React, { useContext, useEffect, useState } from "react";
import {
  CONTACT_US_BUTTON_LINK,
  DATA_STORE_LINK,
  DOCUMENTATION_BASE_URL,
  JOB_LIST_ROUTE,
  JOB_ROUTE_PREFIX,
  JobSubRouteComponent,
  NavListItem,
  PROV_STORE_LINK,
  ProfileIcon,
  ProtectedRoute,
  REGISTRY_LINK,
  SideNavBox,
} from "react-libs";
import { Footer } from "react-libs/components/Footer";
import { Link, Route, Switch } from "react-router-dom";
import { ThemeConfigContext } from "../index";
import Admin from "../pages/Admin";
import Introduction from "../pages/Introduction";
import Profile from "../pages/Profile";
import accessStore from "../stores/accessStore";
import "./RoutesAndLayout.css";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    page: {
      display: "flex",
      flexDirection: "column",
      minHeight: "100vh",
    },
    root: {
      display: "flex",
      flexGrow: 1,
      backgroundColor: "white",
    },
    container: {
      marginTop: 100,
      marginBottom: 20,
      minHeight: "60vh",
    },
    appBar: {
      zIndex: theme.zIndex.drawer + 1,
      color: "white",
      marginTop: 75,
    },
    appBarContent: {
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
    menuBtn: {
      color: "white",
    },
    appHeader: {
      color: "white",
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
    menuSliderContainer: {
      paddingTop: 200,
      width: 250,
      background: "#7c7c7c",
      height: "100%",
    },
    avatar: {
      margin: "0.5rem auto",
      padding: "1rem",
      width: theme.spacing(13),
      height: theme.spacing(13),
    },
    listItem: {
      color: "white",
    },
  }),
);

function RoutesAndLayout() {
  const classes = useStyles();
  // Pull current theme config
  const themeConfig = useContext(ThemeConfigContext);
  const { keycloak } = useKeycloak();
  const [open, setOpen] = useState(false);

  const SIDE_NAV_LIST_ITEMS: NavListItem[] = [
    {
      listText: "Data Store",
      href: DATA_STORE_LINK,
    },
    {
      listText: "Entity Registry",
      href: REGISTRY_LINK,
    },
    {
      listText: "Provenance Store",
      href: PROV_STORE_LINK,
    },
    {
      listText: themeConfig.hamburgerNavigation.docsName,
      href: themeConfig.hamburgerNavigation.docsLink,
    },
  ];

  const toggleSlider = () => {
    setOpen(!open);
  };

  // Setup conditional admin tab
  var adminTab = null;

  // Make sure authorized - this will fill in the admin access field
  useEffect(() => {
    if (keycloak.authenticated) {
      accessStore.testAccess();
    }
  }, [keycloak.authenticated]);

  if (keycloak.authenticated && accessStore.adminAccess) {
    adminTab = (
      <Button
        component={Link}
        to="/admin"
        className={classes.routerButtonDefault}
      >
        Admin
      </Button>
    );
  } else {
    adminTab = null;
  }

  return (
    <div className={classes.page}>
      <Drawer open={open} anchor="left" onClose={toggleSlider}>
        <SideNavBox navListItems={SIDE_NAV_LIST_ITEMS} />
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
              <Stack direction="row" alignItems="center" spacing={3}>
                <IconButton onClick={toggleSlider} className={classes.menuBtn}>
                  <Menu />
                </IconButton>
                <Link to="/">
                  <Typography
                    variant="h6"
                    component="div"
                    className={classes.appHeader}
                    textAlign="center"
                    alignItems="center"
                  >
                    {themeConfig.currentPageThemeConfig.appBarTitle}
                  </Typography>
                </Link>
              </Stack>
              <Stack
                direction="row"
                alignItems="center"
                divider={<Divider orientation="vertical" flexItem />}
              >
                <Button
                  component={Link}
                  to="/introduction"
                  className={classes.routerButtonDefault}
                >
                  Introduction
                </Button>
                {adminTab}
                <Button
                  component={Link}
                  to={JOB_LIST_ROUTE}
                  className={classes.routerButtonDefault}
                >
                  Jobs
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
            <Route exact path="/" component={Introduction} />
            <Route exact path="/introduction" component={Introduction} />
            <ProtectedRoute path="/profile">
              <Profile />
            </ProtectedRoute>
            <ProtectedRoute path="/admin">
              <Admin />
            </ProtectedRoute>
            <ProtectedRoute path="/admin" component={Admin} />
            {
              // Generic shared job routes
            }
            <ProtectedRoute path={JOB_ROUTE_PREFIX}>
              <JobSubRouteComponent></JobSubRouteComponent>
            </ProtectedRoute>
          </Switch>
        </Container>
      </div>
      <Footer {...themeConfig.footerConfig} />
    </div>
  );
}

export default observer(RoutesAndLayout);
