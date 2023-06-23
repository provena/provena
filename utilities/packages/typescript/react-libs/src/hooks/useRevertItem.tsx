import { useQuery } from "@tanstack/react-query";
import { ItemSubType } from "../shared-interfaces/RegistryModels";
import { revertItem } from "../queries";
import { ItemRevertResponse } from "../shared-interfaces/RegistryAPI";
import {
    LoadedEntity,
    mapQueryToLoadedEntity,
} from "../interfaces/hookInterfaces";

export interface UseRevertItemProps {
    id?: string;
    historyId?: number;
    reason?: string;
    subtype?: ItemSubType;
    onSuccess?: (response: ItemRevertResponse) => void;
}
export interface UseRevertItemOutput {
    submit?: () => void;
    response?: LoadedEntity<ItemRevertResponse>;
    dataReady: boolean;
}
export const useRevertItem = (
    props: UseRevertItemProps
): UseRevertItemOutput => {
    /**
    Hook: useRevertItem

    Manages the restoring of an item to a desired historical ID.

    Uses react query with a non auto fetching query - exposing relevant info.
    */

    // Ensure all required items are present
    const requiredItems = [
        props.id,
        props.historyId,
        props.reason,
        props.subtype,
    ];
    const dataReady = !requiredItems.some((i) => {
        return i === undefined;
    });

    // Manage query which is either update or create
    const revertQuery = useQuery({
        queryKey: [
            "revertitem",
            props.subtype,
            props.id,
            props.historyId,
            props.reason,
        ],
        queryFn: () => {
            return revertItem({
                id: props.id!,
                historyId: props.historyId!,
                reason: props.reason!,
                subtype: props.subtype!,
            });
        },
        retry: false,
        refetchOnMount: false,
        enabled: false,
        onSuccess(data) {
            if (props.onSuccess !== undefined) {
                props.onSuccess(data);
            }
        },
    });

    const submit = () => {
        revertQuery.refetch();
    };

    // Return the result and submitter
    return {
        dataReady,
        submit: dataReady ? submit : undefined,
        response: dataReady
            ? {
                  data: revertQuery.data,
                  ...mapQueryToLoadedEntity(revertQuery),
              }
            : undefined,
    };
};
