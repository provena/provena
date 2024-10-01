import {
  Alert,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { AccessStatusDisplayComponent } from "components/AccessStatusDisplay";
import { ModelRunForm } from "components/ModelRunForm";
import { useCreateModelRun } from "hooks/modelRunOps";
import { ModelRunRecord } from "provena-interfaces/RegistryModels";
import { useState } from "react";
import {
  AutoCompleteDatasetLookup,
  AutoCompleteDatasetTemplateLookup,
  AutoCompleteModelRunWorkflowDefinitionLookup,
  AutoCompleteOrganisationLookup,
  AutoCompletePersonLookup,
  AutoCompleteStudyLookup,
  DatasetTemplateAdditionalAnnotationsOverride,
  Form,
  REGISTER_MODEL_RUN_WORKFLOW_DEFINITION,
  useAccessCheck,
  WorkflowVisualiserComponent,
} from "react-libs";

const useStyles = makeStyles((theme: Theme) => createStyles({}));

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

interface MonitorResultComponentProps {
  createTask: ReturnType<typeof useCreateModelRun>;
}
const MonitorResultComponent = (props: MonitorResultComponentProps) => {
  /**
    Component: MonitorResultComponent

    Shows and monitors results of model run lodge or update.    
    */

  const createSessionId = props.createTask.create?.data?.session_id;
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
    <div>
      {header}
      {content}
    </div>
  );
};

export const CreateModelRunTool = () => {
  /**
    Component: LodgeComponent

    Lodge form page. Allows updating or creating a new record.
    
    */
  const [formData, setFormData] = useState<object>({});
  const [showResult, setShowResult] = useState<boolean>(false);

  // Manage form submission with create/edit hooks
  const createManager = useCreateModelRun({ data: formData as ModelRunRecord });

  // Authorisation check
  const auth = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "WRITE",
  });

  const granted = !!auth.granted;
  const showCreateForm = granted;

  const clear = () => {
    setFormData({});
    setShowResult(false);
  };

  return (
    <Stack direction="column" divider={<Divider flexItem={true} />} spacing={3}>
      {!granted && (
        <AccessStatusDisplayComponent
          accessCheck={auth}
        ></AccessStatusDisplayComponent>
      )}
      {showCreateForm && (
        <ModelRunForm
          formData={formData ?? {}}
          onSubmit={() => {
            console.log(JSON.stringify(formData));
            // create new record
            createManager.create?.mutate();
            setShowResult(true);
          }}
          setFormData={setFormData}
          submitEnabled={true}
        />
      )}
      {showResult && (
        <MonitorResultComponent
          createTask={createManager}
        ></MonitorResultComponent>
      )}
    </Stack>
  );
};
