import { useMutation } from "@tanstack/react-query";
import { ItemBase } from "../shared-interfaces/RegistryAPI";
import { createNewVersion } from "../queries";

export interface UseCreateNewVersionProps {}
export interface CreateNewVersionMutateProps {
    item: ItemBase;
    reason: string;
}

export const useCreateNewVersion = (props: UseCreateNewVersionProps) => {
    /**
    Hook: useCreateNewVersion

    Manage the creation for a new version of current item.

    current item must be the latest item.
    
    */

    const createNewVersionMutate = useMutation({
        mutationFn: (props: CreateNewVersionMutateProps) => {
            return createNewVersion({
                subtype: props.item.item_subtype,
                data: { id: props.item.id, reason: props.reason },
            });
        },
    });

    // Return the result and submitter
    return createNewVersionMutate;
};
