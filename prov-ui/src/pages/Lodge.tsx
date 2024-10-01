import {
  Alert,
  AlertTitle,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { ItemModelRun } from "provena-interfaces/RegistryAPI";
import { cloneDeep } from "lodash";
import { useEffect, useState } from "react";
import {
  AutoCompleteDatasetLookup,
  AutoCompleteDatasetTemplateLookup,
  AutoCompleteModelLookup,
  AutoCompleteModelRunWorkflowDefinitionLookup,
  AutoCompleteOrganisationLookup,
  AutoCompletePersonLookup,
  AutoCompleteStudyLookup,
  DatasetTemplateAdditionalAnnotationsOverride,
  deriveResourceAccess,
  filteredNoneDeepCopy,
  Form,
  REGISTER_MODEL_RUN_WORKFLOW_DEFINITION,
  ResourceAccess,
  SubtypeSearchSelector,
  useAccessCheck,
  useTypedLoadedItem,
  useWorkflowManager,
  WorkflowVisualiserComponent,
} from "react-libs";
import { useCreateModelRun, useUpdateModelRun } from "hooks/modelRunOps";
import { ModelRunRecord } from "provena-interfaces/RegistryModels";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    interactionContainer: {
      paddingTop: theme.spacing(2),
      paddingLeft: theme.spacing(1),
    },
    interactionPanel: {
      display: "flex",
      justifyContent: "space-around",
      alignItems: "center",
      backgroundColor: "white",
      padding: theme.spacing(2),
      borderRadius: 5,
    },
    mainActionButton: {
      marginBottom: theme.spacing(2),
      width: "40%",
    },
    stackContainer: {
      backgroundColor: "white",
      borderRadius: 5,
      paddingLeft: theme.spacing(4),
      paddingRight: theme.spacing(4),
      paddingTop: theme.spacing(2),
      paddingBottom: theme.spacing(2),
    },
    root: {
      padding: theme.spacing(3),
      backgroundColor: theme.palette.background.paper,
      borderRadius: theme.shape.borderRadius,
    },
    button: {
      minWidth: 200,
      minHeight: 100,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      textTransform: "none",
    },
    activeButton: {
      backgroundColor: theme.palette.common.white,
      color: theme.palette.common.white,
      borderRadius: theme.shape.borderRadius,
      border: `4px solid ${theme.palette.primary.main}`,
      "&:hover": {
        backgroundColor: theme.palette.primary.dark[50],
        borderRadius: theme.shape.borderRadius,
        border: `4px solid ${theme.palette.primary.main}`,
      },
    },
    inactiveButton: {
      backgroundColor: theme.palette.common.white,
      color: theme.palette.primary.main,
      "&:hover": {
        backgroundColor: theme.palette.primary.light,
        color: theme.palette.common.white,
        borderRadius: theme.shape.borderRadius,
        border: `2px solid ${theme.palette.primary.main}`,
      },
    },
    icon: {
      fontSize: 40,
      marginBottom: theme.spacing(1),
      color: theme.palette.primary.main,
    },
  })
);

// TODO get from prov-api
const JSON_SCHEMA = {
  type: "object",
  definitions: {
    datasetItem: {
      type: "object",
      properties: {
        dataset_type: {
          type: "string",
          enum: ["DATA_STORE"],
          default: "DATA_STORE",
        },
        dataset_template_id: { type: "string" },
        dataset_id: { type: "string" },
        resources: {
          type: "object",
          additionalProperties: { type: "string" },
        },
      },
      required: ["dataset_template_id", "dataset_id", "dataset_type"],
    },
  },
  properties: {
    workflow_template_id: { type: "string" },
    model_version: { type: "string" },
    inputs: {
      type: "array",
      items: { $ref: "#/definitions/datasetItem" },
    },
    outputs: {
      type: "array",
      items: { $ref: "#/definitions/datasetItem" },
    },
    annotations: {
      type: "object",
      additionalProperties: { type: "string" },
    },
    start_time: { type: "number" },
    end_time: { type: "number" },
    display_name: { type: "string" },
    description: { type: "string" },
    study_id: { type: "string" },
    associations: {
      type: "object",
      properties: {
        modeller_id: { type: "string" },
        requesting_organisation_id: { type: "string" },
      },
      required: ["modeller_id"],
    },
  },
  required: [
    "workflow_template_id",
    "inputs",
    "outputs",
    "display_name",
    "description",
    "associations",
    "start_time",
    "end_time",
  ],
};
const DISPLAY_NAME_LABEL =
  "Enter a brief name, label or title for this resource.";

const DS_SPEC = {
  "ui:title": "Input Dataset Information",
  dataset_template_id: {
    "ui:title": "Dataset Template",
    "ui:description":
      "Use the search tool below to select the registered dataset template from the workflow template.",
    "ui:field": "autoCompleteDatasetTemplateLookup",
  },
  dataset_id: {
    "ui:title": "Dataset",
    "ui:description":
      "Use the search tool below to select the dataset which satisfies this template.",
    "ui:field": "autoCompleteDatasetLookup",
  },
  resources: {
    "ui:title": "Resources",
    "ui:description":
      "If your template requires specification of resources within the dataset, use the tool below to add them.",
  },
};

const UI_SCHEMA = {
  "ui:title": "Model Run Record",
  display_name: {
    "ui:description": DISPLAY_NAME_LABEL,
  },
  workflow_template_id: {
    "ui:title": "Workflow Template",
    "ui:description":
      "Select a registered workflow template from the search tool below.",
    "ui:field": "autoCompleteWorkflowTemplateLookup",
  },
  study_id: {
    "ui:title": "Study",
    "ui:description": "Select a registered study from the search tool below.",
    "ui:field": "autoCompleteStudyLookup",
  },
  inputs: {
    "ui:title": "Input Datasets",
    "ui:description":
      "Provide an input dataset for each of the model run's templated inputs.",
    items: DS_SPEC,
  },
  outputs: {
    "ui:title": "Output Datasets",
    "ui:description":
      "Provide an output dataset for each of the model run's templated outputs.",
    items: DS_SPEC,
  },
  associations: {
    "ui:title": "Associations",
    "ui:description":
      "A set of associations about people or organisations involved in this model run record.",
    modeller_id: {
      "ui:title": "Modeller",
      "ui:description":
        "Use the search tool below to select the Person who ran this model.",
      "ui:field": "autoCompletePersonLookup",
    },
    requesting_organisation_id: {
      "ui:title": "Organisation",
      "ui:description":
        "Use the search tool below to select the Organisation who is responsible for this model run.",
      "ui:field": "autoCompleteOrganisationLookup",
    },
  },
};

interface SelectLodgeModeComponentProps {
  lodgeMode: LodgeMode;
  setLodgeMode: (mode: LodgeMode) => void;
}
const SelectLodgeModeComponent = (props: SelectLodgeModeComponentProps) => {
  /**
    Component: SelectLodgeModeComponent

    Allows the user to select from the lodge modes i.e. lodge a new model run OR
    edit an existing model run

    */
  const { lodgeMode, setLodgeMode } = props;
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <Stack direction="row" spacing={3} justifyContent="center">
        <Button
          variant="outlined"
          className={`${classes.button} ${
            lodgeMode === "create" ? classes.activeButton : ""
          }`}
          onClick={() => setLodgeMode("create")}
        >
          <span className={classes.icon}>+</span>
          <Typography variant="subtitle1">Create New Model Run</Typography>
        </Button>
        <Button
          variant="outlined"
          className={`${classes.button} ${
            lodgeMode === "update" ? classes.activeButton : ""
          }`}
          onClick={() => setLodgeMode("update")}
        >
          <span className={classes.icon}>✎</span>
          <Typography variant="subtitle1">Edit Existing Model Run</Typography>
        </Button>
      </Stack>
    </div>
  );
};

const customFields: { [name: string]: any } = {
  // e.g.
  autoCompleteDatasetTemplateLookup: AutoCompleteDatasetTemplateLookup,
  autoCompleteWorkflowTemplateLookup:
    AutoCompleteModelRunWorkflowDefinitionLookup,
  autoCompleteDatasetLookup: AutoCompleteDatasetLookup,
  autoCompleteStudyLookup: AutoCompleteStudyLookup,
  autoCompletePersonLookup: AutoCompletePersonLookup,
  autoCompleteOrganisationLookup: AutoCompleteOrganisationLookup,
  datasetTemplateMetadataOverride: DatasetTemplateAdditionalAnnotationsOverride,
};

interface ReasonInputComponentProps {
  reason: string;
  setReason: (reason: string) => void;
}
const ReasonInputComponent = (props: ReasonInputComponentProps) => {
  /**
    Component: ReasonInputComponent
    Provides a wrapper around the reason when updating
    */
  const classes = useStyles();
  return (
    <div>
      <Stack direction="column" spacing={2}>
        <Typography variant="subtitle1">
          Please provide an explanation for why this update is required*
        </Typography>
        <TextField
          fullWidth
          placeholder={"Why are you updating this item?"}
          required={true}
          multiline
          value={props.reason}
          onChange={(e) => {
            props.setReason(e.target.value);
          }}
        />
      </Stack>
    </div>
  );
};

interface AccessStatusDisplayComponentProps {
  accessCheck: ReturnType<typeof useAccessCheck>;
}
const AccessStatusDisplayComponent = (
  props: AccessStatusDisplayComponentProps
) => {
  /**
    Component: AccessStatusDisplayComponent

    Displays the loading/status of the access check - only used in the case that
    access is not yet granted
    */
  const classes = useStyles();
  const status = props.accessCheck;
  var content: JSX.Element = <p></p>;

  if (status.loading) {
    content = (
      <Stack justifyContent="center" direction="row">
        <CircularProgress />;
      </Stack>
    );
  } else if (status.error) {
    content = (
      <Alert severity={"error"}>
        <AlertTitle>Error</AlertTitle>
        <p>
          {" "}
          An error occurred while retrieving access information. Error:{" "}
          {status.errorMessage ?? "Unknown"}. <br />
          If you cannot determine how to fix this issue, try refreshing, or
          contact us to get help.
        </p>
      </Alert>
    );
  } else if (!status.error && !status.loading && !status.granted) {
    content = <p>Access not granted</p>;
  } else {
    content = <p>Access granted</p>;
  }

  return <div>{content}</div>;
};

interface ModelRunFormProps {
  jsonSchema: {};
  uiSchema: {};
  formData: {};
  setFormData: (formData: object) => void;
  onSubmit: () => void;
  submitEnabled: boolean;
  submitDisabledReason?: string;
}
const ModelRunForm = (props: ModelRunFormProps) => {
  /**
    Component: RegisterUpdateForm
    
    Contains the auto generated form. Provides interface into the state.

    This is a controlled component.
    */

  // css styling
  const classes = useStyles();

  return (
    <div className={classes.stackContainer}>
      <Form
        schema={props.jsonSchema as RJSFSchema}
        uiSchema={{
          ...props.uiSchema,
          // Forces the form to always include the top level object
          disableOptional: true,
        }}
        fields={customFields}
        // TODO
        widgets={{}}
        formData={props.formData}
        validator={validator}
        onChange={(d) => {
          props.setFormData(d.formData);
        }}
        onSubmit={(form) => {
          props.onSubmit();
        }}
      >
        <Grid container item xs={12}>
          <Grid container item xs={12} className={classes.interactionContainer}>
            <Grid
              container
              item
              xs={12}
              className={classes.interactionPanel}
              direction="row"
            >
              <Button
                variant="outlined"
                href="/"
                className={classes.mainActionButton}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                type="submit"
                className={classes.mainActionButton}
                disabled={!props.submitEnabled}
              >
                Submit
              </Button>
            </Grid>
            {!props.submitEnabled &&
              props.submitDisabledReason !== undefined && (
                <Grid item xs={12}>
                  <Alert variant="outlined" severity="warning">
                    {props.submitDisabledReason}
                  </Alert>
                </Grid>
              )}
          </Grid>
        </Grid>
      </Form>
    </div>
  );
};

interface AlertErrorComponentProps {
  title: string;
  errorContent: JSX.Element;
}
const AlertErrorComponent = (props: AlertErrorComponentProps) => {
  /**
    Component: AlertErrorComponent

    Generic error display component which renders nicely in register form

    */
  const classes = useStyles();
  return (
    <div className={classes.stackContainer}>
      <Alert
        severity="error"
        variant="outlined"
        className={classes.stackContainer}
      >
        <AlertTitle>{props.title}</AlertTitle>
        {props.errorContent}
      </Alert>
    </div>
  );
};

interface SelectModelRunComponentProps {
  modelRunId: string | undefined;
  setLoadedModelRun: (modelRun: ItemModelRun | undefined) => void;
  setWriteAccess: (hasAccess: boolean | undefined) => void;
  onSelected: (id: string | undefined) => void;
}
const SelectModelRunComponent = (props: SelectModelRunComponentProps) => {
  /**
    Component: SelectModelRunComponent

    Select an existing model run to edit.
    */

  // Hook to load typed item
  const {
    item: typedItem,
    data: typedPayload,
    loading: typedLoading,
    error: typedIsError,
    errorMessage: typedErrorMessage,
    refetch: refetchLoadedItem,
  } = useTypedLoadedItem({
    id: props.modelRunId,
    subtype: "MODEL_RUN",
    enabled: !!props.modelRunId,
  });

  // Need to derive this access when the item is fetched
  const [resourceAccess, setResourceAccess] = useState<
    ResourceAccess | undefined
  >(undefined);

  useEffect(() => {
    if (typedPayload !== undefined) {
      const access = deriveResourceAccess(typedPayload.roles ?? []);
      props.setWriteAccess(access?.writeMetadata);
      props.setLoadedModelRun(typedItem as ItemModelRun);
    } else {
      props.setWriteAccess(undefined);
      props.setLoadedModelRun(undefined);
    }
  }, [typedPayload]);

  return (
    <>
      <SubtypeSearchSelector
        description="Select an existing model run to update it's details."
        subtypePlural="Model Runs"
        required={true}
        selectedId={props.modelRunId}
        setSelectedId={props.onSelected}
        subtype="MODEL_RUN"
        title="Select a Model Run"
        persistTitle={true}
      />
    </>
  );
};

interface RenderRegisterWorkflowComponentProps {
  session_id: string;
}
const RenderRegisterWorkflowComponent = (
  props: RenderRegisterWorkflowComponentProps
) => {
  /**
    Component: RenderRegisterWorkflowComponent
    */
  return (
    <WorkflowVisualiserComponent
      adminMode={false}
      enableExpand={true}
      startingSessionID={props.session_id}
      workflowDefinition={REGISTER_MODEL_RUN_WORKFLOW_DEFINITION}
      direction="column"
    ></WorkflowVisualiserComponent>
  );
};

interface RenderUpdateWorkflowComponentProps {
  session_id: string;
}
const RenderUpdateWorkflowComponent = (
  props: RenderUpdateWorkflowComponentProps
) => {
  /**
    Component: RenderUpdateWorkflowComponent
    */
  return (
    <WorkflowVisualiserComponent
      adminMode={false}
      enableExpand={true}
      startingSessionID={props.session_id}
      workflowDefinition={REGISTER_MODEL_RUN_WORKFLOW_DEFINITION}
      direction="column"
    ></WorkflowVisualiserComponent>
  );
};

interface MonitorResultComponentProps {
  lodgeMode: LodgeMode;
  createTask: ReturnType<typeof useCreateModelRun>;
  updateTask: ReturnType<typeof useUpdateModelRun>;
}
const MonitorResultComponent = (props: MonitorResultComponentProps) => {
  /**
    Component: MonitorResultComponent

    Shows and monitors results of model run lodge or update.    
    */

  const createSessionId = props.createTask.create?.data?.session_id;
  const updateSessionId = props.updateTask.update?.data?.session_id;
  if (props.lodgeMode === "create") {
    const header = <Typography variant="h6">Creation Results</Typography>;
    let content;
    if (props.createTask.create?.isLoading) {
      content = <CircularProgress />;
    } else if (props.createTask.create?.isError) {
      content = (
        <Typography variant="caption" color="red">
          {props.createTask.create.error ?? "Unknown error occurred."}
        </Typography>
      );
    } else if (createSessionId) {
      content = (
        <>
          <RenderRegisterWorkflowComponent
            session_id={createSessionId}
          ></RenderRegisterWorkflowComponent>
        </>
      );
    }
    return (
      <>
        {header}
        {content}
      </>
    );
  } else {
    const header = <Typography variant="h6">Update Results</Typography>;
    let content;
    if (props.createTask.create?.isLoading) {
      content = <CircularProgress />;
    } else if (props.createTask.create?.isError) {
      content = (
        <Typography variant="caption" color="red">
          {props.createTask.create.error ?? "Unknown error occurred."}
        </Typography>
      );
    } else if (createSessionId) {
      content = (
        <>
          <RenderUpdateWorkflowComponent
            session_id={createSessionId}
          ></RenderUpdateWorkflowComponent>
        </>
      );
    }
    return (
      <>
        {header}
        {content}
      </>
    );
  }
};

type LodgeMode = "create" | "update";

export interface LodgeComponentProps {}
export const LodgeComponent = (props: LodgeComponentProps) => {
  /**
    Component: LodgeComponent

    Lodge form page. Allows updating or creating a new record.
    
    */
  // TODO Destub

  const [modelRunId, setModelRunId] = useState<string | undefined>(undefined);
  const [lodgeMode, setLodgeMode] = useState<LodgeMode>("create");
  const [modelRunRecord, setModelRunRecord] = useState<
    ItemModelRun | undefined
  >(undefined);
  const [formData, setFormData] = useState<object>({});
  const [reason, setReason] = useState<string | undefined>(undefined);
  const [canWriteToRecord, setCanWriteToRecord] = useState<boolean | undefined>(
    undefined
  );

  // Authorisation check
  const auth = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "WRITE",
  });

  const granted = !!auth.granted;

  const showUpdateForm = granted && lodgeMode === "update" && canWriteToRecord;
  const showCreateForm = granted && lodgeMode === "create";

  useEffect(() => {
    // TODO replace with useFormSetup once API returns the data - this is hack!
    if (
      lodgeMode === "update" &&
      Object.keys(formData).length === 0 &&
      !!modelRunRecord
    ) {
      console.log("Updating form data");
      console.log(JSON.stringify(modelRunRecord.record));
      setFormData(filteredNoneDeepCopy(modelRunRecord.record));
    }
  }, [modelRunRecord]);

  const clear = () => {
    setFormData({});
    setModelRunId(undefined);
    setModelRunRecord(undefined);
    setReason(undefined);
    setShowResult(false);
  };

  // Manage form submission with create/edit hooks
  const createManager = useCreateModelRun({ data: formData as ModelRunRecord });
  const updateManager = useUpdateModelRun({
    data: formData as ModelRunRecord,
    reason,
    modelRunId,
  });

  const [showResult, setShowResult] = useState<boolean>(false);

  return (
    <Stack direction="column" divider={<Divider flexItem={true} />} spacing={3}>
      {!granted && (
        <AccessStatusDisplayComponent
          accessCheck={auth}
        ></AccessStatusDisplayComponent>
      )}
      <SelectLodgeModeComponent
        lodgeMode={lodgeMode}
        setLodgeMode={(mode) => {
          setLodgeMode(mode);
          clear();
        }}
      />
      {granted && (
        <>
          {lodgeMode === "update" && (
            <SelectModelRunComponent
              modelRunId={modelRunId}
              onSelected={(id) => {
                clear();
                setModelRunId(id);
              }}
              setLoadedModelRun={setModelRunRecord}
              setWriteAccess={setCanWriteToRecord}
            />
          )}
          {showUpdateForm && (
            <ReasonInputComponent reason={reason ?? ""} setReason={setReason} />
          )}
          {(showUpdateForm || showCreateForm) && (
            <ModelRunForm
              formData={formData ?? {}}
              jsonSchema={JSON_SCHEMA}
              onSubmit={() => {
                console.log(JSON.stringify(formData));
                if (lodgeMode === "create") {
                  // create new record
                  createManager.create?.mutate();
                  setShowResult(true);
                } else {
                  // update existing record
                  updateManager.update?.mutate();
                  setShowResult(true);
                }
              }}
              setFormData={setFormData}
              submitEnabled={lodgeMode === "create" || ("update" && !!reason)}
              uiSchema={UI_SCHEMA}
              submitDisabledReason="Must provide a reason before updating this record"
            />
          )}
        </>
      )}
      {showResult && (
        <MonitorResultComponent
          createTask={createManager}
          updateTask={updateManager}
          lodgeMode={lodgeMode}
        ></MonitorResultComponent>
      )}
    </Stack>
  );
};
