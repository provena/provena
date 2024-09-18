import { useMutation } from "@tanstack/react-query";
import { addStudyLink, LoadedEntity } from "react-libs";
import { AddStudyLinkResponse } from "react-libs/provena-interfaces/AsyncJobAPI";

export interface UseAddStudyLinkProps {
  modelRunId?: string;
  studyId?: string;
  onSuccess?: (response: AddStudyLinkResponse) => void;
}
export interface UseAddStudyLinkOutput {
  submit?: () => void;
  response?: LoadedEntity<AddStudyLinkResponse>;
  dataReady: boolean;
}
export const useAddStudyLink = (
  props: UseAddStudyLinkProps
): UseAddStudyLinkOutput => {
  /**
    Hook: useAddStudyLink

    Adds a study link to an existing model run.

    Uses react query with mutation - exposing relevant info.
    */

  // Ensure all required items are present
  const requiredItems = [props.modelRunId, props.studyId];
  const dataReady = !requiredItems.some((i) => {
    return i === undefined;
  });

  // Manage query which is either update or create
  const addStudyLinkQuery = useMutation({
    mutationFn: () => {
      return addStudyLink({
        modelRunId: props.modelRunId!,
        studyId: props.studyId!,
      });
    },
    onSuccess(data) {
      if (props.onSuccess !== undefined) {
        props.onSuccess(data);
      }
    },
  });

  const submit = () => {
    addStudyLinkQuery.mutate();
  };

  // Return the result and submitter
  return {
    dataReady,
    submit: dataReady ? submit : undefined,
    response: dataReady
      ? {
          data: addStudyLinkQuery.data,
          loading: addStudyLinkQuery.isLoading,
          error: addStudyLinkQuery.isError,
          success: addStudyLinkQuery.isSuccess,
          errorMessage: addStudyLinkQuery.error
            ? (addStudyLinkQuery.error as string)
            : undefined,
        }
      : undefined,
  };
};
