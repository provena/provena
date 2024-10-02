import {
  Button,
  CircularProgress,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { AccessStatusDisplayComponent } from "components/AccessStatusDisplay";
import { ModelRunForm } from "components/ModelRunForm";
import { SelectWorkflowTemplateComponent } from "components/Selectors";
import { useCreateModelRun } from "hooks/modelRunOps";
import { ItemModelRunWorkflowTemplate } from "provena-interfaces/AuthAPI";
import { ModelRunRecord } from "provena-interfaces/RegistryModels";
import { useEffect, useState } from "react";
import {
  REGISTER_MODEL_RUN_WORKFLOW_DEFINITION,
  useAccessCheck,
  WorkflowVisualiserComponent,
} from "react-libs";

const useStyles = makeStyles((theme: Theme) => createStyles({}));

const generatePrefillFromTemplate = (
  template: ItemModelRunWorkflowTemplate
): object => {
  // Returns a partial prefill of form data based on template contents
  // TODO prefill the resources by fetching all templates
  return {
    workflow_template_id: template.id,
    inputs: template.input_templates
      ? template.input_templates.map((dataset_template) => {
          return {
            dataset_template_id: dataset_template.template_id,
            dataset_type: "DATA_STORE",
          };
        })
      : [],
    outputs: template.output_templates
      ? template.output_templates.map((template) => {
          return {
            dataset_template_id: template.template_id,
            dataset_type: "DATA_STORE",
          };
        })
      : [],
  };
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

interface MonitorResultComponentProps {
  createTask: ReturnType<typeof useCreateModelRun>;
  onDismissError: () => void;
}
const MonitorResultComponent = (props: MonitorResultComponentProps) => {
  /**
    Component: MonitorResultComponent

    Shows and monitors results of model run lodge or update.    
    */

  const task = props.createTask?.create;
  const createSessionId = task?.data?.session_id;
  const header = <Typography variant="h6">Creation Results</Typography>;
  let content;
  if (props.createTask.create?.isLoading) {
    content = <CircularProgress />;
  } else if (task?.isError) {
    content = (
      <Stack spacing={2} alignContent="flex-start">
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
  const [workflowId, setWorkflowId] = useState<string | undefined>(undefined);
  const [workflow, setWorkflow] = useState<
    ItemModelRunWorkflowTemplate | undefined
  >(undefined);
  // Manage form submission with create/edit hooks
  const createManager = useCreateModelRun({ data: formData as ModelRunRecord });

  // Authorisation check
  const auth = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "WRITE",
  });

  const granted = !!auth.granted;
  const showSelectTemplate = granted && !workflow;
  const showCreateForm = granted && !!workflow;

  useEffect(() => {
    // TODO replace with useFormSetup once API returns the data - this is hack!
    if (Object.keys(formData).length === 0 && !!workflow) {
      console.log("Updating form data with workflow template results");
      const prefillData = generatePrefillFromTemplate(workflow);
      console.log("Prefill data: ");
      console.log(JSON.stringify(prefillData));
      setFormData(prefillData);
    }
  }, [workflow]);

  const clear = () => {
    setFormData({});
    setShowResult(false);
    setWorkflow(undefined);
    setWorkflowId(undefined);
  };

  return (
    <Stack direction="column" divider={<Divider flexItem={true} />} spacing={3}>
      <Stack direction="column" spacing={1}>
        <Stack
          direction="row"
          justifyContent={"space-between"}
          alignItems="center"
        >
          <Typography variant="h4">Create a new Model Run</Typography>
          <Button onClick={clear} variant="outlined" color="warning">
            Start again
          </Button>
        </Stack>
        <Typography variant="subtitle1">
          This tool provides a form in which you can create a new model run. Get
          started by selecting the workflow template you'd like to create a new
          Model Run for.
        </Typography>
      </Stack>

      {!granted && (
        <AccessStatusDisplayComponent
          accessCheck={auth}
        ></AccessStatusDisplayComponent>
      )}
      {showSelectTemplate && (
        <SelectWorkflowTemplateComponent
          workflowTemplateId={workflowId}
          onSelected={(id) => {
            clear();
            setWorkflowId(id);
          }}
          setLoadedWorkflow={setWorkflow}
          // No need to worry about this right now
          setWriteAccess={() => {}}
        ></SelectWorkflowTemplateComponent>
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
          onCancel={clear}
        />
      )}
      {showResult && (
        <MonitorResultComponent
          createTask={createManager}
          onDismissError={() => {
            setShowResult(false);
          }}
        ></MonitorResultComponent>
      )}
    </Stack>
  );
};
