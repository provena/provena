import { WorkflowDefinition } from "../hooks";
import { ItemBase } from "../provena-interfaces/RegistryModels";
import {
  CREATE_WORKFLOW_DEFINITION,
  VERSION_WORKFLOW_DEFINITION,
} from "./jobWorkflowDefinitions";

interface WorkflowParserOutputs {
  startingSessionId?: string;
  workflowDefinition?: WorkflowDefinition;
}

interface WorkflowParserProps {
  item?: ItemBase;
}

export const workflowItemParser = (
  props: WorkflowParserProps,
): WorkflowParserOutputs => {
  // This function helps initial values need for rendering WorkflowVisualiser View
  const createSessionId =
    props.item?.workflow_links?.create_activity_workflow_id;

  const versionSessionId =
    props.item?.workflow_links?.version_activity_workflow_id;

  // Initial Workflow view props
  const startingSessionId: string | undefined =
    createSessionId ?? versionSessionId ?? undefined;

  const workflowDefinition: WorkflowDefinition | undefined = createSessionId
    ? CREATE_WORKFLOW_DEFINITION
    : versionSessionId
      ? VERSION_WORKFLOW_DEFINITION
      : undefined;

  return { startingSessionId, workflowDefinition };
};
