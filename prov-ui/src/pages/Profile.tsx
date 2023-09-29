import { Box, Button, Grid, Tab, Tabs, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { observer } from "mobx-react-lite";
import { useState } from "react";
import {
    TabPanel,
    CopyFloatingButton,
    BoundedContainer,
    DOCUMENTATION_BASE_URL,
    LANDING_PAGE_LINK_PROFILE,
} from "react-libs";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            padding: theme.spacing(4),
            backgroundColor: "white",
            minHeight: "60vh",
            display: "flex",
            flexDirection: "row",
            alignContent: "start",
            borderRadius: 5,
        },
        tabPanel: {
            paddingLeft: theme.spacing(4),
            "& span": {
                marginLeft: 10,
            },
        },
        refreshTokenMsg: {
            color: "green",
            fontSize: "16px",
        },
    })
);

const Profile = observer(() => {
    const classes = useStyles();
    const [currentTab, setCurrentTab] = useState(0);
    const { keycloak, initialized } = useKeycloak();
    return (
        <BoundedContainer breakpointKey={"lg"}>
            <Grid container item xs={12} className={classes.root}>
                <Grid item xs={12}>
                    <Typography variant="h3" id="profile-title" align="center">
                        Profile
                    </Typography>
                </Grid>
                <Grid item xs={2}>
                    <Box sx={{ borderRight: 1, borderColor: "divider" }}>
                        <Tabs
                            orientation="vertical"
                            value={currentTab}
                            onChange={(e, value) => setCurrentTab(value)}
                        >
                            <Tab label="Profile" key="profile" />
                            <Tab label="Roles" key="roles" />
                            <Tab label="Token" key="token" />
                            <Tab label="Logout" key="logout" />
                        </Tabs>
                    </Box>
                </Grid>
                <Grid item xs={10} className={classes.tabPanel}>
                    <TabPanel index={0} currentIndex={currentTab}>
                        <h3>User Name</h3>
                        {keycloak.tokenParsed
                            ? keycloak.tokenParsed.name
                            : "Details loading..."}
                        <h3>User Email</h3>
                        {keycloak.tokenParsed
                            ? keycloak.tokenParsed.email
                            : "Details loading..."}
                        <h3>Authorization</h3>
                        You can use the{" "}
                        <a href={LANDING_PAGE_LINK_PROFILE} target="_blank">
                            Landing Portal
                        </a>{" "}
                        to request system authorisation.
                        <br />
                        For more information, visit{" "}
                        <a
                            href={
                                DOCUMENTATION_BASE_URL +
                                "/getting-started-is/requesting-access-is.html"
                            }
                            target="_blank"
                        >
                            our documentation
                        </a>
                        .
                    </TabPanel>
                    <TabPanel index={1} currentIndex={currentTab}>
                        <h3>Roles</h3>
                        <Grid item xs={12}>
                            <Typography variant="body1">
                                You can manage your provenance store access
                                roles at the{" "}
                                <a
                                    href={LANDING_PAGE_LINK_PROFILE}
                                    target={"_blank"}
                                >
                                    Landing Portal.
                                </a>{" "}
                                <br />
                                For more information, visit{" "}
                                <a
                                    href={
                                        DOCUMENTATION_BASE_URL +
                                        "/getting-started-is/requesting-access-is.html"
                                    }
                                    target="_blank"
                                >
                                    our documentation
                                </a>
                                .
                            </Typography>
                        </Grid>
                    </TabPanel>
                    <TabPanel index={2} currentIndex={currentTab}>
                        <h3>Token</h3>
                        <div
                            style={{
                                wordWrap: "break-word",
                                color: "#333",
                                padding: "10px",
                                backgroundColor: "#F5F5F5",
                                border: "1px solid #ccc",
                                borderRadius: "4px",
                            }}
                        >
                            <CopyFloatingButton
                                clipboardText={keycloak.token || ""}
                            />
                            {keycloak.token || "None"}
                        </div>
                    </TabPanel>
                    <TabPanel index={3} currentIndex={currentTab}>
                        <h3>Logout</h3>
                        <Button
                            variant="outlined"
                            onClick={() => keycloak.logout()}
                        >
                            Logout
                        </Button>
                    </TabPanel>
                </Grid>
            </Grid>
        </BoundedContainer>
    );
});

export default Profile;
