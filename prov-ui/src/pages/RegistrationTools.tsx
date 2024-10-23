import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  Stack,
  Tab,
  Tabs,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import { observer } from "mobx-react-lite";
import React, { useEffect, useState } from "react";
import accessStore from "../stores/accessStore";
import GenerateTemplate from "../subpages/GenerateTemplate";
import LodgeTemplate from "../subpages/LodgeTemplate";

import KeyboardArrowLeftIcon from "@mui/icons-material/KeyboardArrowLeft";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import { BoundedContainer } from "react-libs";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      display: "flex",
      backgroundColor: theme.palette.common.white,
      marginBottom: theme.spacing(4),
      minHeight: "60vh",
      alignContent: "start",
      padding: theme.spacing(4),
      borderRadius: 5,
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
  }),
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

const RegistrationTools = observer(() => {
  const classes = useStyles();
  const [currentTab, setCurrentTab] = useState(0);
  const [sideBar, setSideBar] = useState(true);
  const { keycloak, initialized } = useKeycloak();

  // Firstly - make sure we have access
  useEffect(() => {
    accessStore.checkAccess();
  }, [keycloak.authenticated]);

  const handleCollapse = () => {
    setSideBar(!sideBar);
  };

  if (!initialized) {
  }

  // Define the error dialog fragment in case something goes wrong with the
  // access check process
  const dialogFragment = (
    <React.Fragment>
      {
        //Error dialogue based on store state
      }
      <Dialog open={accessStore.error}>
        <DialogTitle> Access check error! </DialogTitle>
        <DialogContent>
          <DialogContent>
            <p>
              The system experienced an issue while trying to check your system
              access. <br />
              Error message:{" "}
              {accessStore.errorMessage ?? "No error message provided."}
              <br />
              Press <i>Dismiss</i> to attempt interacting with the prov store
              anyway. If you are definitely authorised and still see this error,
              please use the <i>Contact Us</i> link to report an issue.
            </p>
          </DialogContent>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => accessStore.dismissError()}>Dismiss</Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );

  // If there is an issue with access, prompt re-login
  if (accessStore.loading) {
    return (
      <div className={classes.root}>
        <CircularProgress />
      </div>
    );
  }

  if (!(accessStore.registryWriteAccess || accessStore.forceErrorBypass)) {
    return (
      <div className={classes.root}>
        <Stack
          spacing={2}
          justifyContent="flex-start"
          style={{ width: "100%" }}
          alignItems="center"
        >
          <Alert severity="warning">
            You do not have write permission to the provenance store.
          </Alert>
          <Button variant="outlined" onClick={() => keycloak.logout()}>
            Logout
          </Button>
        </Stack>
      </div>
    );
  }
  if (!(accessStore.registryReadAccess || accessStore.forceErrorBypass)) {
    return (
      <div className={classes.root}>
        <Stack
          spacing={2}
          justifyContent="flex-start"
          style={{ width: "100%" }}
          alignItems="center"
        >
          <Alert severity="warning">
            You do not have sufficient permission to read from the entity
            registry!
          </Alert>
          <Button variant="outlined" onClick={() => keycloak.logout()}>
            Logout
          </Button>
        </Stack>
      </div>
    );
  }

  return (
    <BoundedContainer breakpointKey={"xl"}>
      <Grid container xs={12} className={classes.root}>
        <Grid xs={12}>
          <Typography variant="h3" align="center">
            Provenance Registration Tools
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
          <Grid item flexGrow={1}>
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
                    onChange={(e, value) => setCurrentTab(value)}
                  >
                    <Tab
                      label={
                        <Typography
                          variant="subtitle1"
                          align="right"
                          width="100%"
                        >
                          Generate CSV Template
                        </Typography>
                      }
                      key="generatecsvtemplate"
                    />
                    <Tab
                      label={
                        <Typography
                          variant="subtitle1"
                          align="right"
                          width="100%"
                        >
                          Lodge CSV Template
                        </Typography>
                      }
                      key="lodgecsvtemplate"
                    />
                  </Tabs>
                </Box>
              </Grid>
            )}
          </Grid>
          <Grid item xs={sideBar ? 10 : 11.5} className={classes.tabPanel}>
            <TabPanel index={0} currentIndex={currentTab}>
              <GenerateTemplate />
            </TabPanel>
            <TabPanel index={1} currentIndex={currentTab}>
              <LodgeTemplate />
            </TabPanel>
          </Grid>
        </Grid>
      </Grid>
    </BoundedContainer>
  );
});

export default RegistrationTools;
