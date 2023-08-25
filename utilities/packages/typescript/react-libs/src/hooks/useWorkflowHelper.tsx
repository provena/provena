import { useKeycloak } from "@react-keycloak/web";
import { ItemBase } from "../shared-interfaces/RegistryModels";
import { workflowItemParser } from "../util";
import { useAccessCheck } from "./useAccessCheck";
import { WorkflowDefinition } from "./useWorkflowManager";
export interface UseWorkflowHelperProps {
    item?: ItemBase;
}
export interface UseWorkflowHelperOutput {
    workflowDefinition?: WorkflowDefinition;
    startingSessionId?: string;
    visible: boolean;
    adminMode: boolean;
}
export const useWorkflowHelper = (
    props: UseWorkflowHelperProps
): UseWorkflowHelperOutput => {
    /**
    Hook: useWorkflowHelper

    Manages determining workflow definition, starting session id, visibility and
    admin mode for a async workflow.
    */
    const { keycloak } = useKeycloak();
    const item = props.item;

    // Initial values need for rendering WorkflowVisualiser
    const { startingSessionId: startingSessionId, workflowDefinition } =
        workflowItemParser({ item: props.item });

    // Determine if workflow visualiser is visible and if admin mode
    const jobServiceReadCheck = useAccessCheck({
        componentName: "job-service",
        desiredAccessLevel: "READ",
    });

    // This is always defined
    // Implies item -> defined
    const workflowIdentified = !!startingSessionId && !!workflowDefinition;
    const jobServiceRead = jobServiceReadCheck.fallbackGranted;
    console.log("Job service read", jobServiceRead);
    const userOwnsWorkflow =
        item !== undefined &&
        item?.owner_username === keycloak.tokenParsed!.preferred_username;

    // Should admin fetching be used? prefer user fetching
    const adminMode = !userOwnsWorkflow && jobServiceRead;
    // Should workflow be visible
    const visibility =
        workflowIdentified && (userOwnsWorkflow || jobServiceRead);

    return {
        workflowDefinition,
        startingSessionId,
        visible: visibility,
        adminMode,
    };
};
