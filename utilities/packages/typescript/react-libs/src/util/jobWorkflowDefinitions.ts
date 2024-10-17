import { WorkflowDefinition } from "../hooks";
import {
  ProvLodgeModelRunResult,
  RegistryRegisterCreateActivityResult,
  RegistryRegisterVersionActivityResult,
} from "../provena-interfaces/AsyncJobAPI";
import { ProvLodgeModelRunPayload } from "../provena-interfaces/AsyncJobModels";

export const CREATE_WORKFLOW_DEFINITION: WorkflowDefinition = {
  name: "Item Creation Workflow",
  description: "Tracks the registration and provenance of an item's creation",
  steps: [
    // Create activity step
    {
      name: "Register Create Activity",
      shortDescription: "Register create activity",
      nextStepGenerator(resultPayload) {
        // Cast as response type
        const typedResult =
          resultPayload as RegistryRegisterCreateActivityResult;
        return typedResult.lodge_session_id;
      },
    },
    // Lodge created activity step
    {
      name: "Lodge Create Activity Provenance",
      shortDescription: "Lodge Create Activity Provenance",
      // No next step - final entry
    },
  ],
};

export const VERSION_WORKFLOW_DEFINITION: WorkflowDefinition = {
  name: "Item Version Workflow",
  description: "Tracks the registration and provenance of an item version",
  steps: [
    // Create activity step
    {
      name: "Register Version Activity",
      shortDescription: "Register version activity",
      nextStepGenerator(resultPayload) {
        // Cast as response type
        const typedResult =
          resultPayload as RegistryRegisterVersionActivityResult;
        return typedResult.lodge_session_id;
      },
    },
    // Lodge created activity step
    {
      name: "Lodge Version Activity Provenance",
      shortDescription: "Lodge Version Activity Provenance",
      // No next step - final entry
    },
  ],
};

export const REGISTER_MODEL_RUN_WORKFLOW_DEFINITION: WorkflowDefinition = {
  name: "Model Run Registration",
  description: "Tracks the registration and provenance of a model run",
  steps: [
    // Lodge step
    {
      name: "Register and Lodge Provenance",
      shortDescription: "Register model run",
    },
  ],
};

export const UPDATE_MODEL_RUN_WORKFLOW_DEFINITION: WorkflowDefinition = {
  name: "Model Run Update",
  description: "Tracks the update of a model run.",
  steps: [
    // Lodge and update step
    {
      name: "Perform Update",
      shortDescription: "Update model run",
    },
  ],
};
