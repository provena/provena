import { ItemModelRunWorkflowTemplate } from "provena-interfaces/AuthAPI";
import { ItemModelRun as ModelRunWorkflowTemplate } from "provena-interfaces/RegistryAPI";
import { useEffect } from "react";
import {
  deriveResourceAccess,
  SubtypeSearchSelector,
  useTypedLoadedItem,
} from "react-libs";

export interface SelectModelRunComponentProps {
  modelRunId: string | undefined;
  setLoadedModelRun: (modelRun: ModelRunWorkflowTemplate | undefined) => void;
  setWriteAccess: (hasAccess: boolean | undefined) => void;
  onSelected: (id: string | undefined) => void;
}
export const SelectModelRunComponent = (
  props: SelectModelRunComponentProps
) => {
  /**
    Component: SelectModelRunComponent

    Select an existing model run to edit.
    */

  // Hook to load typed item
  const { item: typedItem, data: typedPayload } = useTypedLoadedItem({
    id: props.modelRunId,
    subtype: "MODEL_RUN",
    enabled: !!props.modelRunId,
  });

  useEffect(() => {
    if (typedPayload !== undefined) {
      const access = deriveResourceAccess(typedPayload.roles ?? []);
      props.setWriteAccess(access?.writeMetadata);
      props.setLoadedModelRun(typedItem as ModelRunWorkflowTemplate);
    } else {
      props.setWriteAccess(undefined);
      props.setLoadedModelRun(undefined);
    }
  }, [typedPayload]);

  return (
    <>
      <SubtypeSearchSelector
        description="Select a registered model run."
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

export interface SelectWorkflowTemplateComponentProps {
  workflowTemplateId: string | undefined;
  setLoadedWorkflow: (
    modelRun: ItemModelRunWorkflowTemplate | undefined
  ) => void;
  setWriteAccess: (hasAccess: boolean | undefined) => void;
  onSelected: (id: string | undefined) => void;
}
export const SelectWorkflowTemplateComponent = (
  props: SelectWorkflowTemplateComponentProps
) => {
  /**
    Select a workflow template.
    */

  // Hook to load typed item
  const { item: typedItem, data: typedPayload } = useTypedLoadedItem({
    id: props.workflowTemplateId,
    subtype: "MODEL_RUN_WORKFLOW_TEMPLATE",
    enabled: !!props.workflowTemplateId,
  });

  useEffect(() => {
    if (typedPayload !== undefined) {
      const access = deriveResourceAccess(typedPayload.roles ?? []);
      props.setWriteAccess(access?.writeMetadata);
      props.setLoadedWorkflow(typedItem as ItemModelRunWorkflowTemplate);
    } else {
      props.setWriteAccess(undefined);
      props.setLoadedWorkflow(undefined);
    }
  }, [typedPayload]);

  return (
    <>
      <SubtypeSearchSelector
        description="Select a registered workflow template."
        subtypePlural="Workflow Templates"
        required={true}
        selectedId={props.workflowTemplateId}
        setSelectedId={props.onSelected}
        subtype="MODEL_RUN_WORKFLOW_TEMPLATE"
        title="Select a Workflow Template"
        persistTitle={true}
      />
    </>
  );
};
