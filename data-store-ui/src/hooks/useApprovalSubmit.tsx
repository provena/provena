import { useMutation } from "@tanstack/react-query";
import { approvalRequest } from "react-libs";

interface UseApprovalSubmitMutateProps {
    datasetId: string;
    approverId: string;
    requesterNotes: string;
}

export const useApprovalSubmit = () => {
    /**
    Hook: useApprovalSubmit
    
    For submitting approval request from requester
    */

    const approvalSubmitMutate = useMutation({
        mutationFn: (props: UseApprovalSubmitMutateProps) => {
            return approvalRequest({
                datasetId: props.datasetId,
                approverId: props.approverId,
                requesterNotes: props.requesterNotes,
            });
        },
    });

    return approvalSubmitMutate;
};
