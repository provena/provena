import {
  Button,
  CircularProgress,
  Divider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { AccessStatusDisplayComponent } from "components/AccessStatusDisplay";
import { ModelRunForm } from "components/ModelRunForm";
import { SelectModelRunComponent } from "components/Selectors";
import { useUpdateModelRun } from "hooks/modelRunOps";
import { ItemModelRun } from "provena-interfaces/RegistryAPI";
import { ModelRunRecord } from "provena-interfaces/RegistryModels";
import { useEffect, useState } from "react";
import {
  deriveResourceAccess,
  filteredNoneDeepCopy,
  ResourceAccess,
  SubtypeSearchSelector,
  UPDATE_MODEL_RUN_WORKFLOW_DEFINITION,
  useAccessCheck,
  useTypedLoadedItem,
  WorkflowVisualiserComponent,
} from "react-libs";

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
  onDismissError: () => void;
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
      <Stack spacing={2} alignItems="flex-start">
        <Typography variant="subtitle1" color="red">
          {task?.error ?? "Unknown error occurred."}
        </Typography>
        <Button
          onClick={props.onDismissError}
          fullWidth={false}
          variant="outlined"
        >
          Dismiss
        </Button>
      </Stack>
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

// Optional props to be used if a model run id is to be injected into the component.
interface UpdateModelRunOptionalProps{
  modelRunId?: string
}

export const UpdateModelRunTool = (props: UpdateModelRunOptionalProps | {}) => {
  /**
    Component: UpdateModelRunTool

    Lodge form page. Allows updating an existing record.
    
    */

  // Declare the type of props if provided.  
  const typedProps = props as UpdateModelRunOptionalProps;

  const [modelRunId, setModelRunId] = useState<string | undefined>(undefined);
  const [modelRunRecord, setModelRunRecord] = useState<
    ItemModelRun | undefined
  >(undefined);
  const [formData, setFormData] = useState<object>({});
  const [reason, setReason] = useState<string | undefined>(undefined);
  const [canWriteToRecord, setCanWriteToRecord] = useState<boolean | undefined>(
    undefined
  );
  const [showResult, setShowResult] = useState<boolean>(false);

  // Authorisation check
  const auth = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "WRITE",
  });

  const granted = !!auth.granted;
  const showUpdateForm = granted && canWriteToRecord && !showResult;

  useEffect(() => {
    if (typedProps && typedProps.modelRunId){
      setModelRunId(typedProps.modelRunId)
    }
  }, [])

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

  return (
    <Stack direction="column" divider={<Divider flexItem={true} />} spacing={3}>
      <Stack direction="column" spacing={1}>
        <Stack
          direction="row"
          justifyContent={"space-between"}
          alignItems="center"
        >
          <Typography variant="h4">Update a Model Run</Typography>
          <Button onClick={clear} variant="outlined" color="warning">
            Start again
          </Button>
        </Stack>
        <Typography variant="subtitle1">
          This tool provides a form in which you can update an existing model
          run. To get started, use the search tool below to identify your
          existing model run, or enter the identifier directly.
        </Typography>
      </Stack>
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
              onCancel={clear}
            />
          )}
        </>
      )}
      {showResult && (
        <MonitorResultComponent
          updateTask={updateManager}
          onDismissError={() => {
            setShowResult(false);
          }}
        ></MonitorResultComponent>
      )}
    </Stack>
  );
};
