import { useQuery } from "@tanstack/react-query";
import {
    LoadedEntity,
    assignPersonLink,
    mapQueryToLoadedEntity,
    validatePersonLink,
    LoadedWithRefetch,
} from "react-libs";
import {
    UserLinkUserAssignResponse,
    UserLinkUserValidateResponse,
} from "../shared-interfaces/AuthAPI";

export interface UseValidateAndAssignLinkProps {
    // If provided, validates, required for submission
    personId: string | undefined;
    // Optionally provide a submission on success callback
    onAssignmentSuccess?: () => void;
}

export interface UseValidateAndAssignLinkOutput {
    // Only included if the validation succeeded
    submit: (() => void) | undefined;

    // Is it valid?
    valid: boolean | undefined;

    // Validation occurs automatically when person id is provided
    validationResult:
        | LoadedWithRefetch<UserLinkUserValidateResponse>
        | undefined;

    // Assignment is manual - provide submit func
    submissionResult: LoadedWithRefetch<UserLinkUserAssignResponse> | undefined;
}
export const useValidateAndAssignLink = (
    props: UseValidateAndAssignLinkProps
): UseValidateAndAssignLinkOutput => {
    /**
    Hook: useValidateAndAssignLink

    Manages the auto validation and manual assignment of the user link service Identity
    */

    const dataReady = props.personId !== undefined;

    // Refresh validity every 60s
    const cacheTimeout = 60000;

    // Query to validate person ID
    const validateQuery = useQuery({
        queryKey: ["validateassignment", props.personId ?? "unspecified"],
        queryFn: () => {
            return validatePersonLink({ personId: props.personId ?? "" });
        },
        staleTime: cacheTimeout,
        enabled: dataReady,
    });

    // Query to validate person ID
    const assignQuery = useQuery({
        queryKey: ["userlinkassignment", props.personId ?? "unspecified"],
        queryFn: () => {
            return assignPersonLink({ personId: props.personId ?? "" });
        },
        staleTime: cacheTimeout,
        enabled: false,
        // Optional callback
        onSuccess: () => {
            if (props.onAssignmentSuccess !== undefined) {
                props.onAssignmentSuccess();
            }
        },
    });

    // is valid
    const valid = dataReady ? validateQuery.data?.status.success : undefined;

    return {
        // Derived result - valid?
        valid,

        // Submit func
        submit: !!valid ? assignQuery.refetch : undefined,
        submissionResult: !!valid
            ? {
                  data: assignQuery.data,
                  refetch: assignQuery.refetch,
                  ...mapQueryToLoadedEntity(assignQuery),
              }
            : undefined,

        // Validation part of results
        validationResult: {
            data: validateQuery.data,
            refetch: validateQuery.refetch,
            ...mapQueryToLoadedEntity(validateQuery),
        },
    };
};
