import { useQuery } from "@tanstack/react-query";
import { LoadedEntity, createItem, mapQueryToLoadedEntity } from "react-libs";
import { GenericCreateResponse } from "../provena-interfaces/RegistryAPI";
import {
  DomainInfoBase,
  ItemSubType,
} from "../provena-interfaces/RegistryModels";

export interface UseCreateItemProps {
  subtype?: ItemSubType;
  data?: DomainInfoBase;
  // Can override enabled if applicable
  enabled?: boolean;
}
export interface UseCreateItemOutput {
  // Tries for the first time, or forces a retry
  submit: () => void;
  // If submitted at least once, either contains success or an error
  response: LoadedEntity<GenericCreateResponse>;
}
export const useCreateItem = (
  props: UseCreateItemProps,
): UseCreateItemOutput => {
  /**
    Hook: useCreateItem

    Manages the creation of an entity - provides a submit interface which
    enables manual retrying as in repeated submit scenario (forms).

    The useCreateItem and useUpdateItem hooks are similar. 

    Both do not have any auto fetching/caching/refetching and are driven
    entirely on event by the refetch trigger.
    */

  // Combined enabled
  const dataReady = props.subtype !== undefined && props.data !== undefined;

  // Manage query which is either update or create
  const createQuery = useQuery({
    queryKey: ["createitem", props.subtype],
    queryFn: () => {
      console.log("Submitting");
      // We know these are defined as we have checked
      return createItem({
        data: props.data!,
        subtype: props.subtype!,
      });
    },
    retry: false,
    refetchOnMount: false,
    enabled: false,
  });

  const submit = () => {
    console.log(JSON.stringify(props));
    if (dataReady) {
      createQuery.refetch();
    }
  };

  // Return the result and submitter
  return {
    submit,
    response: {
      data: createQuery.data,
      ...mapQueryToLoadedEntity(createQuery),
    },
  };
};
