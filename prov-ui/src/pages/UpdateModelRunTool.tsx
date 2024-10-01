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
  UPDATE_MODEL_RUN_WORKFLOW_DEFINITION,
  useAccessCheck,
  useTypedLoadedItem,
  useWorkflowManager,
  WorkflowVisualiserComponent,
} from "react-libs";
import { useCreateModelRun, useUpdateModelRun } from "hooks/modelRunOps";
import { ModelRunRecord } from "provena-interfaces/RegistryModels";
import { AccessStatusDisplayComponent } from "components/AccessStatusDisplay";
import { ModelRunForm } from "components/ModelRunForm";

const useStyles = makeStyles((theme: Theme) => createStyles({}));

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
      workflowDefinition={UPDATE_MODEL_RUN_WORKFLOW_DEFINITION}
      direction="column"
    ></WorkflowVisualiserComponent>
  );
};

interface MonitorResultComponentProps {
  updateTask: ReturnType<typeof useUpdateModelRun>;
}
const MonitorResultComponent = (props: MonitorResultComponentProps) => {
  /**
    Component: MonitorResultComponent

    Shows and monitors results of model run lodge or update.    
    */

  const updateSessionId = props.updateTask.update?.data?.session_id;
  const header = <Typography variant="h6">Update Results</Typography>;
  const task = props.updateTask?.update;
  let content;
  if (task?.isLoading) {
    content = <CircularProgress />;
  } else if (task?.isError) {
    content = (
      <Typography variant="caption" color="red">
        {task?.error ?? "Unknown error occurred."}
      </Typography>
    );
  } else if (updateSessionId) {
    content = (
      <>
        <RenderUpdateWorkflowComponent
          session_id={updateSessionId}
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
};

export const UpdateModelRunTool = () => {
  /**
    Component: UpdateModelRunTool

    Lodge form page. Allows updating an existing record.
    
    */
  // TODO Destub

  const [modelRunId, setModelRunId] = useState<string | undefined>(undefined);
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
  const showUpdateForm = granted && canWriteToRecord;

  useEffect(() => {
    // TODO replace with useFormSetup once API returns the data - this is hack!
    if (Object.keys(formData).length === 0 && !!modelRunRecord) {
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
      {granted && (
        <>
          <SelectModelRunComponent
            modelRunId={modelRunId}
            onSelected={(id) => {
              clear();
              setModelRunId(id);
            }}
            setLoadedModelRun={setModelRunRecord}
            setWriteAccess={setCanWriteToRecord}
          />
          {showUpdateForm && (
            <ReasonInputComponent reason={reason ?? ""} setReason={setReason} />
          )}
          {showUpdateForm && (
            <ModelRunForm
              formData={formData ?? {}}
              onSubmit={() => {
                console.log(JSON.stringify(formData));
                // update existing record
                updateManager.update?.mutate();
                setShowResult(true);
              }}
              setFormData={setFormData}
              submitEnabled={!!reason}
              submitDisabledReason="Must provide a reason before updating this record"
            />
          )}
        </>
      )}
      {showResult && (
        <MonitorResultComponent
          updateTask={updateManager}
        ></MonitorResultComponent>
      )}
    </Stack>
  );
};
