import { useQuery } from "@tanstack/react-query";
import { LoadedEntity, mapQueryToLoadedEntity, updateItem } from "react-libs";
import { StatusResponse } from "../provena-interfaces/RegistryAPI";
import {
  DomainInfoBase,
  ItemSubType,
} from "../provena-interfaces/RegistryModels";

export interface UseUpdateItemProps {
  // Id to update
  id?: string;
  // Subtype
  subtype?: ItemSubType;
  // The data to submit
  data?: DomainInfoBase;
  // Why is this update being performed?
  reason?: string;
  // Can override enabled if applicable
  enabled?: boolean;
}
export interface UseUpdateItemOutput {
  // Tries for the first time, or forces a retry
  submit: () => void;
  // If submitted at least once, either contains success or an error
  response: LoadedEntity<StatusResponse>;
}
export const useUpdateItem = (
  props: UseUpdateItemProps,
): UseUpdateItemOutput => {
  /**
    Hook: useUpdateItem

    Manages the update of an entity - provides a submit interface which enables
    manual retrying as in repeated submit scenario (forms).

    The useCreateItem and useUpdateItem hooks are similar. 

    Both do not have any auto fetching/caching/refetching and are driven
    entirely on event by the refetch trigger.
    */

  // Ensure all required fields are populated
  const requiredFields = [props.id, props.subtype, props.data, props.reason];
  const dataReady = !requiredFields.some((i) => i === undefined);

  // Manage query which is either update or create
  const updateQuery = useQuery({
    queryKey: ["updateitem", props.id ?? "noid", props.subtype],
    queryFn: () => {
      // We know these are defined as we have checked
      return updateItem({
        id: props.id!,
        data: props.data!,
        subtype: props.subtype!,
        reason: props.reason!,
      });
    },
    retry: false,
    refetchOnMount: false,
    enabled: false,
  });

  const submit = () => {
    if (dataReady) {
      updateQuery.refetch();
    }
  };

  // Return the result and submitter
  return {
    submit,
    response: {
      data: updateQuery.data,
      ...mapQueryToLoadedEntity(updateQuery),
    },
  };
};
