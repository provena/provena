import React, { useState } from "react";
import {
    Alert,
    Grid,
    Tabs,
    Tab,
    Box,
    Typography,
    Backdrop,
    CircularProgress,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import makeStyles from "@mui/styles/makeStyles";
import { RouteComponentProps, Link as RouteLink } from "react-router-dom";
import createStyles from "@mui/styles/createStyles";
import { observer } from "mobx-react-lite";
import accessStore from "../stores/accessStore";
import { useKeycloak } from "@react-keycloak/web";

// Tab components
import { LogoutView } from "../components/LogoutView";
import { TokenOverview } from "../components/TokenOverview";
import { ProfileOverview } from "../components/ProfileOverview";
import { RoleRequests } from "../components/RoleRequests";
import { BoundedContainer, useQueryStringVariable } from "react-libs";
import { UserLinkWorkflowComponent } from "../subpages/UserLinkWorkflow";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            padding: theme.spacing(4),
            display: "flex",
            minHeight: "60vh",
            flexDirection: "row",
            alignContent: "start",
            borderRadius: 5,
        },
        tabPanel: {
            paddingLeft: theme.spacing(4),
        },
        refreshTokenMsg: {
            color: "green",
            fontSize: "16px",
            marginLeft: 10,
        },
    })
);
interface TabPanelProps {
    children: React.ReactNode;
    index: string;
    currentIndex: string;
}

const TabPanel = (props: TabPanelProps) => (
    <div hidden={props.currentIndex !== props.index} key={props.index}>
        {props.currentIndex === props.index && <>{props.children}</>}
    </div>
);

interface ProfileProps {}

type Views = "profile" | "roles" | "token" | "logout" | "identity";
interface TabInterface {
    label: string;
    to: Views;
    component: JSX.Element;
}

const Profile = observer((props: ProfileProps) => {
    const classes = useStyles();
    const { keycloak, initialized } = useKeycloak();

    const defaultView: Views = "profile";
    const qStringKey = "function";
    const { value: currentTabRaw, setValue: setCurrentTab } =
        useQueryStringVariable({
            queryStringKey: qStringKey,
            readOnly: false,
            defaultValue: defaultView,
        });

    const currentTab = currentTabRaw! as Views;

    const tabs: Array<TabInterface> = [
        {
            label: "Profile",
            to: "profile",
            component: <ProfileOverview />,
        },
        {
            label: "Identity",
            to: "identity",
            component: <UserLinkWorkflowComponent />,
        },
        {
            label: "Roles",
            to: "roles",
            component: <RoleRequests />,
        },
        {
            label: "Token",
            to: "token",
            component: <TokenOverview />,
        },
        {
            label: "Logout",
            to: "logout",
            component: <LogoutView />,
        },
    ];

    return (
        <BoundedContainer breakpointKey={"lg"}>
            <Grid container xs={12} className={classes.root}>
                <Grid xs={12}>
                    <Typography variant="h3" id="profile-title" align="center">
                        Profile
                    </Typography>
                </Grid>
                {accessStore.accessCheckMsg && (
                    <Alert severity="warning">
                        {accessStore.accessCheckMsg}
                    </Alert>
                )}
                <Grid xs={2}>
                    <Box sx={{ borderRight: 1, borderColor: "divider" }}>
                        <Tabs
                            orientation="vertical"
                            value={currentTab}
                            onChange={(e, value) => {
                                setCurrentTab!(value);
                            }}
                        >
                            {tabs.map((tabInterface) => (
                                <Tab
                                    label={tabInterface.label}
                                    value={tabInterface.to}
                                    component={RouteLink}
                                    to={`/profile?${qStringKey}=${tabInterface.to}`}
                                />
                            ))}
                        </Tabs>
                    </Box>
                </Grid>
                {!keycloak.tokenParsed || !keycloak.authenticated ? (
                    <Backdrop open={true}>
                        <CircularProgress />
                    </Backdrop>
                ) : (
                    <Grid xs={10} className={classes.tabPanel}>
                        {tabs.map((tabInterface) => (
                            <TabPanel
                                index={tabInterface.to}
                                currentIndex={currentTab}
                            >
                                {tabInterface.component}
                            </TabPanel>
                        ))}
                    </Grid>
                )}
            </Grid>
        </BoundedContainer>
    );
});

export default Profile;
