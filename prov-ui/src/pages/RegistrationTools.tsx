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
import { BoundedContainer, useTypedQueryStringVariable } from "react-libs";
import { CreateModelRunTool } from "./CreateModelRunTool";
import { UpdateModelRunTool } from "./UpdateModelRunTool";

export const TOOL_TAB_IDS = {
  GENERATE_TEMPLATE: 0,
  LODGE_TEMPLATE: 1,
  CREATE: 2,
  EDIT: 3,
};

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

const RegistrationTools = observer(() => {
  const classes = useStyles();
  const [currentTab, setCurrentTab] = useState(0);
  const [sideBar, setSideBar] = useState(true);
  const { keycloak, initialized } = useKeycloak();

  // Parent component holds the requested edit model run id.
  const [modelRunId, setModelRunId] = useState<string | undefined>(undefined);

  // Query string parser for model run record Id
  const { value: modelRunIdQString, setValue: setModelRunIdQString } =
    useTypedQueryStringVariable({
      queryStringKey: "recordId",
      defaultValue: undefined,
    });

  // useEffect to change form tabs if query string exists and strip off the
  // model run record id
  useEffect(() => {
    if (modelRunIdQString !== undefined) {
      // move to model run edit tab
      setCurrentTab(TOOL_TAB_IDS.EDIT);
      setModelRunId(modelRunIdQString);
      // Value of the query string is stripped, to prevent persistent auto-complete of the forms.
      setModelRunIdQString?.(undefined);
    }
  }, [modelRunIdQString]);

  // Firstly - make sure we have access
  useEffect(() => {
    accessStore.checkAccess();
  }, [keycloak.authenticated]);

  const handleCollapse = () => {
    setSideBar(!sideBar);
  };

  if (!initialized) {
  }

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
                    <Tab
                      label={
                        <Typography
                          variant="subtitle1"
                          align="right"
                          width="100%"
                        >
                          Register Model Run
                        </Typography>
                      }
                      key="createrecord"
                    />
                    <Tab
                      label={
                        <Typography
                          variant="subtitle1"
                          align="right"
                          width="100%"
                        >
                          Update Model Run
                        </Typography>
                      }
                      key="updaterecord"
                    />
                  </Tabs>
                </Box>
              </Grid>
            )}
          </Grid>
          <Grid item xs={sideBar ? 10 : 11.5} className={classes.tabPanel}>
            <TabPanel
              index={TOOL_TAB_IDS.GENERATE_TEMPLATE}
              currentIndex={currentTab}
            >
              <GenerateTemplate />
            </TabPanel>
            <TabPanel
              index={TOOL_TAB_IDS.LODGE_TEMPLATE}
              currentIndex={currentTab}
            >
              <LodgeTemplate />
            </TabPanel>
            <TabPanel index={TOOL_TAB_IDS.CREATE} currentIndex={currentTab}>
              <CreateModelRunTool />
            </TabPanel>
            <TabPanel index={TOOL_TAB_IDS.EDIT} currentIndex={currentTab}>
              <UpdateModelRunTool
                modelRunId={modelRunId}
                reset={() => setModelRunId(undefined)}
              ></UpdateModelRunTool>
            </TabPanel>
          </Grid>
        </Grid>
      </Grid>
    </BoundedContainer>
  );
});

export default RegistrationTools;
