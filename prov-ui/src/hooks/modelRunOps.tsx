import { InputSharp } from "@material-ui/icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  allDefined,
  createItem,
  mapQueryToLoadedEntity,
  registerModelRunRecord,
  updateModelRunRecord,
} from "react-libs";
import { ModelRunRecord } from "react-libs/provena-interfaces/ProvenanceAPI";

export interface UseCreateModelRunProps {
  data?: ModelRunRecord;
}
export const useCreateModelRun = (props: UseCreateModelRunProps) => {
  /**
    Hook: useCreateModelRun

    Submission of new model run records.
    */

  // Combined enabled
  const dataReady = props.data !== undefined;

  // Manage query which is either update or create
  const create = useMutation({
    mutationFn: async () => {
      return await registerModelRunRecord({
        record: props.data!,
      });
    },
  });

  // Return the result and submitter
  if (!dataReady) {
    return { ready: false };
  } else {
    return { ready: true, create };
  }
};

export interface UpdateModelRunProps {
  data?: ModelRunRecord;
  reason?: string;
  modelRunId?: string;
}
export const useUpdateModelRun = (props: UpdateModelRunProps) => {
  /**
    Hook: useCreateModelRun

    Update of model run record
    */

  // Combined enabled
  const dataReady = allDefined([props.data, props.modelRunId, props.reason]);

  // Manage query which is either update or create
  const update = useMutation({
    mutationFn: async () => {
      return await updateModelRunRecord({
        model_run_id: props.modelRunId!,
        reason: props.reason!,
        record: props.data!,
      });
    },
  });

  // Return the result and submitter
  if (!dataReady) {
    return { ready: false };
  } else {
    return { ready: true, update };
  }
};
