import { useQueries } from "@tanstack/react-query";
import { useState } from "react";
import { LoadedEntity, mapQueryToLoadedEntity } from "../interfaces";
import { GetJobResponse } from "../shared-interfaces/AsyncJobAPI";
import { getJobBySessionId } from "../queries";

// IO payloads are a Dict[str, Any] in Python - converted below
type GenericPayload = { [k: string]: any };

// Generator functions take an output payload and generate a session ID, where found
type NextStepGeneratorFunc = (
    resultPayload: GenericPayload
) => string | undefined;

export interface WorkflowStep {
    // A workflow step is metadata + a possible next step generator

    // Metadata
    // --------

    name: string;
    shortDescription: string;

    // Functional
    // ----------

    // How to get to next step? Only undefined if final step
    nextStepGenerator?: NextStepGeneratorFunc;
}

export interface ResolvedSessionInfo {
    sessionId: string;
    // Error might happen even job is successfully queried
    workflowError?: string;
    // Any acton we could provide to user to fix error
    actionMessage?: string;
}

export interface WorkflowDefinition {
    name: string;
    description: string;

    // A workflow is a list of workflow steps and some metadata
    steps: Array<WorkflowStep>;
}

export interface UseWorkflowManagerProps {
    // Definition
    workflowDefinition: WorkflowDefinition;
    // Starting point
    startingSessionId: string;
    // Admin mode - do we fetch using admin endpoint?
    adminMode: boolean;
}

// A list of queries
export interface WorkflowDataResponseItem
    extends LoadedEntity<GetJobResponse | undefined> {
    isAutoRefetching: boolean;
}
export type WorkflowData = Array<WorkflowDataResponseItem>;

// Just returns the dynamic managed list of queries
export interface UseWorkflowManagerOutput {
    // Resulting data chain
    workflowData?: WorkflowData;
    // Is the job complete?
    complete: boolean;
    // Was it all successful?
    success: boolean;
    // Any error?
    error: boolean;
    // Refetch all queries manually
    refetchAll: () => void;
    // Other message needed for rendering ui
    sessionInfo: Array<ResolvedSessionInfo>;
}

export const useWorkflowManager = (
    props: UseWorkflowManagerProps
): UseWorkflowManagerOutput => {
    /**
    Hook: useWorkflowManager
    
    Manages fetching all required data for a specified workflow
    */

    // Manage a dynamic array of fetches cached by session ID as defined by the
    // workflow steps

    // We have chicken and egg situation so need raised state to manage queries
    const [resolvedSessionInfoList, setResolvedSessionInfoList] = useState<
        Array<ResolvedSessionInfo>
    >([{ sessionId: props.startingSessionId }]);

    const [enabledRefetch, setEnabledRefetch] = useState<boolean>(true);

    // Determine the query list based on resolved session Ids
    const refreshInterval = 3000; // ms
    // Always type to match useQuery
    type QueryRefetchType = "always";
    const workflowQueryData = useQueries({
        queries: resolvedSessionInfoList.map((session, index) => {
            return {
                queryKey: ["jobfetch", session.sessionId],
                queryFn: () => {
                    return getJobBySessionId({
                        sessionId: session.sessionId,
                        adminMode: props.adminMode,
                    });
                },
                enabled: enabledRefetch,
                // Never timeout cache due to auto refetch on non resolved state
                staleTime: Infinity,
                // Pointless cast to please typescript gods
                refetchOnMount: "always" as QueryRefetchType,
                refetchInterval: (data: any, query: any) => {
                    // If disabled, stop refetching
                    if (!enabledRefetch) {
                        return false;
                    }
                    try {
                        const typedData = data as GetJobResponse;
                        if (
                            typedData.job.status === "SUCCEEDED" ||
                            typedData.job.status === "FAILED"
                        ) {
                            return false;
                        } else {
                            return refreshInterval;
                        }
                    } catch {
                        return refreshInterval;
                    }
                },
                // When successful query, possibly update resolved id list to fetch next step
                onSuccess: (data: GetJobResponse) => {
                    // When successful - we need to use the next step generator to update the resolved session ID list
                    if (data.job.status !== "SUCCEEDED") {
                        return;
                    }

                    // Check that we are on last resolved step
                    if (index + 1 < resolvedSessionInfoList.length) {
                        // We have already passed this point - no need to do it again
                        return;
                    }

                    // Get next step generator
                    const gen =
                        props.workflowDefinition.steps[index].nextStepGenerator;

                    if (!gen) {
                        console.log(
                            "No next step found - must be completed workflow."
                        );
                        return;
                    }

                    // check there is a result payload
                    if (!data.job.result) {
                        console.error(
                            "Successful job didn't include a result payload!"
                        );
                        // Update error for current session
                        const workflowError =
                            "Successful job didn't include a result payload!";
                        const actionMessage =
                            "Please contact an administrator to check the result payload.";
                        resolvedSessionInfoList[index].workflowError =
                            workflowError;
                        resolvedSessionInfoList[index].actionMessage =
                            actionMessage;

                        return;
                    }

                    // Use the generator to pull the next step
                    const nextStepId = gen(data.job.result);

                    // If the next step is undefined - this is an error state
                    if (!nextStepId) {
                        console.error(
                            "Successful job failed retrieval of next step session ID."
                        );
                        // Update error for current session
                        const workflowError =
                            "This job succeeded, but we couldn't determine the next workflow step";
                        const actionMessage =
                            "Please contact an administrator to check the next workflow step.";
                        resolvedSessionInfoList[index].workflowError =
                            workflowError;
                        resolvedSessionInfoList[index].actionMessage =
                            actionMessage;
                        return;
                    }

                    // Update the resolved session list with new ID
                    const newResolvedSessionInfoList: Array<ResolvedSessionInfo> =
                        JSON.parse(JSON.stringify(resolvedSessionInfoList));

                    newResolvedSessionInfoList.push({ sessionId: nextStepId });

                    setResolvedSessionInfoList(newResolvedSessionInfoList);
                },
                // Catch error case
                onError: (err: any) => {
                    // Error occurred when getting current data,
                    // no possible to get next session id from current data, stop infinity refetching
                    setEnabledRefetch(false);
                },
            };
        }),
    });

    const resolvedWorkflowData: WorkflowData = workflowQueryData.map((data) => {
        return {
            // An item is auto refetching if that item is NOT in either
            // FAILED/SUCCEEDED and refetching is enabled
            isAutoRefetching:
                ["FAILED", "SUCCEEDED"].indexOf(data.data?.job.status ?? "") ===
                    -1 && enabledRefetch,
            data: data.data,
            ...mapQueryToLoadedEntity(data),
        };
    });

    const complete =
        resolvedWorkflowData.length === props.workflowDefinition.steps.length;

    const success = resolvedWorkflowData.every((item) => {
        return item.success && item.data?.job.status === "SUCCEEDED";
    });

    const error = resolvedWorkflowData.some((item) => {
        return item.error || item.data?.job.status === "FAILED";
    });

    const refetchAll = () => {
        setEnabledRefetch(true);
        workflowQueryData.forEach((item) => {
            item.refetch();
        });
    };

    return {
        workflowData: resolvedWorkflowData,
        complete,
        success,
        error,
        refetchAll,
        sessionInfo: resolvedSessionInfoList,
    };
};
