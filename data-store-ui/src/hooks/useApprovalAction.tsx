import { useMutation } from "@tanstack/react-query";
import { approvalAction } from "react-libs";

interface UseApprovalActionMutateProps {
  datasetId: string;
  approve: boolean;
  approverNote: string;
}

export const useApprovalAction = () => {
  /**
    Hook: useApprovalAction
    
    For posting approval action from approver
    */

  const approvalActionMutate = useMutation({
    mutationFn: (props: UseApprovalActionMutateProps) => {
      return approvalAction({
        datasetId: props.datasetId,
        approve: props.approve,
        approverNote: props.approverNote,
      });
    },
  });

  return approvalActionMutate;
};
