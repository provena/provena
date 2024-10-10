import {
  Button,
  CircularProgress,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import { AccessStatusDisplayComponent } from "components/AccessStatusDisplay";
import { ModelRunForm } from "components/ModelRunForm";
import { SelectWorkflowTemplateComponent } from "components/Selectors";
import { useCreateModelRun } from "hooks/modelRunOps";
import { useExploredTemplate } from "hooks/useExploredTemplate";
import {
  ItemBase,
  ItemModelRunWorkflowTemplate,
} from "provena-interfaces/AuthAPI";
import { ModelRunRecord } from "provena-interfaces/RegistryModels";
import { useEffect, useRef, useState } from "react";
import {
  REGISTER_MODEL_RUN_WORKFLOW_DEFINITION,
  useAccessCheck,
  WorkflowVisualiserComponent,
} from "react-libs";
import { BoxedItemDisplayComponent } from "react-libs/components/BoxedItemDisplay";

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

interface DisplayTemplateComponentProps {
  template: ItemModelRunWorkflowTemplate;
}
const DisplayTemplateComponent = (props: DisplayTemplateComponentProps) => {
  /**
    Component: DisplayTemplateComponent
    
    */
  return (
    <Stack spacing={2}>
      <Typography variant="h5">
        Selected Workflow Template: '{props.template.display_name}'
      </Typography>
      <Typography variant="subtitle1">
        Explore details about your selected template below.
      </Typography>
      <BoxedItemDisplayComponent
        item={props.template as unknown as ItemBase}
        layout="column"
      />
    </Stack>
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

  // Load the template and associated entities + generate prefill
  const prefillOp = useExploredTemplate({ workflowTemplateId: workflowId });
  const workflow = prefillOp.query.data?.workflowTemplate;
  const prefill = prefillOp.query.data?.prefill;

  // Manage form submission with create/edit hooks
  const createManager = useCreateModelRun({ data: formData as ModelRunRecord });

  // Authorisation check
  const auth = useAccessCheck({
    componentName: "entity-registry",
    desiredAccessLevel: "WRITE",
  });

  const granted = !!auth.granted;
  const showSelectTemplate = granted && !workflowId && !workflow;
  const showCreateForm = granted && !!workflowId && !!workflow;

  const prefilledRef = useRef<boolean>(false);

  useEffect(() => {
    if (!prefilledRef.current && !!prefill) {
      console.log("Updating form data with workflow template prefill");
      console.log("Prefill data: ");
      console.log(JSON.stringify(prefill));
      setFormData(prefill);

      // Mark as already prefilled
      prefilledRef.current = true;
    }
  }, [prefill]);

  const resetInputs = () => {
    setShowResult(false);
    prefilledRef.current = false;
  };

  useEffect(() => {
    if (!workflowId) {
      setFormData({});
    }
    resetInputs();
  }, [workflowId]);

  return (
    <Stack direction="column" divider={<Divider flexItem={true} />} spacing={3}>
      <Stack direction="column" spacing={1}>
        <Stack
          direction="row"
          justifyContent={"space-between"}
          alignItems="center"
        >
          <Typography variant="h4">Create a new Model Run</Typography>
          <Button
            onClick={() => {
              resetInputs();
              setWorkflowId(undefined);
            }}
            variant="outlined"
            color="warning"
          >
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
          onSelected={setWorkflowId}
          // No need to worry about this right now
          setWriteAccess={() => {}}
        ></SelectWorkflowTemplateComponent>
      )}
      {!!workflow && (
        <DisplayTemplateComponent
          template={workflow}
        ></DisplayTemplateComponent>
      )}
      {prefillOp.query.isInitialLoading ? (
        <CircularProgress></CircularProgress>
      ) : (
        showCreateForm && (
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
            onCancel={resetInputs}
          />
        )
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
