import React, { useState } from "react";
import { useKeycloak } from "@react-keycloak/web";
import {
    Alert,
    Button,
    Grid,
    Tabs,
    Tab,
    IconButton,
    Box,
    Typography,
} from "@mui/material";
import { observer } from "mobx-react-lite";
import accessStore from "../stores/accessStore";
import { ManageAccessRequests } from "../subpages/AdminAccessControl";
import { GroupControl } from "../subpages/AdminGroupControl";
import makeStyles from "@mui/styles/makeStyles";
import createStyles from "@mui/styles/createStyles";
import { Theme } from "@mui/material/styles";

import KeyboardArrowLeftIcon from "@mui/icons-material/KeyboardArrowLeft";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import { BoundedContainer } from "react-libs";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            padding: theme.spacing(4),
            display: "flex",
        },
        tabPanel: {
            paddingLeft: theme.spacing(4),
        },
        button: {
            marginRight: theme.spacing(1),
        },
        instructions: {
            marginTop: theme.spacing(1),
            marginBottom: theme.spacing(1),
        },
    })
);

interface TabPanelProps {
    children: React.ReactNode;
    index: number;
    currentIndex: number;
}

const TabPanel = (props: TabPanelProps) => (
    <div hidden={props.currentIndex !== props.index} key={props.index}>
        {props.currentIndex === props.index && <>{props.children}</>}
    </div>
);

const Admin = observer(() => {
    const classes = useStyles();
    const [currentTab, setCurrentTab] = useState(0);
    const [sideBar, setSideBar] = useState(true);
    const { keycloak, initialized } = useKeycloak();

    const handleCollapse = () => {
        setSideBar(!sideBar);
    };

    // If there is an issue with access, prompt re-login
    if (accessStore.accessCheckMsg) {
        return (
            <div>
                <Alert severity="warning">{accessStore.accessCheckMsg}</Alert>
                <div>
                    <Button
                        variant="outlined"
                        onClick={() => keycloak.logout()}
                    >
                        Logout
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <BoundedContainer breakpointKey={"lg"}>
            <Grid container xs={12} className={classes.root}>
                <Grid xs={12}>
                    <Typography variant="h3" align="center">
                        Admin Console
                    </Typography>
                </Grid>
                <Grid xs={12}>
                    <Grid item>
                        <IconButton onClick={handleCollapse}>
                            {sideBar ? (
                                <KeyboardArrowLeftIcon
                                    fontSize={"large"}
                                ></KeyboardArrowLeftIcon>
                            ) : (
                                <KeyboardArrowRightIcon
                                    fontSize={"large"}
                                ></KeyboardArrowRightIcon>
                            )}
                        </IconButton>
                    </Grid>
                </Grid>
                <Grid container xs={12} flexWrap="nowrap">
                    <Grid item>
                        {sideBar && (
                            <Grid item xs={12}>
                                <Box
                                    sx={{
                                        borderRight: 1,
                                        borderColor: "divider",
                                    }}
                                >
                                    <Tabs
                                        orientation="vertical"
                                        value={currentTab}
                                        onChange={(e, value) =>
                                            setCurrentTab(value)
                                        }
                                    >
                                        <Tab
                                            label="Access Control"
                                            key="accesscontrol"
                                        />
                                        <Tab
                                            label="Group Management"
                                            key="groupmanagement"
                                        />
                                    </Tabs>
                                </Box>
                            </Grid>
                        )}
                    </Grid>
                    <Grid item flexGrow={1} className={classes.tabPanel}>
                        <TabPanel index={0} currentIndex={currentTab}>
                            <ManageAccessRequests></ManageAccessRequests>
                        </TabPanel>
                        <TabPanel index={1} currentIndex={currentTab}>
                            <GroupControl></GroupControl>
                        </TabPanel>
                    </Grid>
                </Grid>
            </Grid>
        </BoundedContainer>
    );
});

export default Admin;
