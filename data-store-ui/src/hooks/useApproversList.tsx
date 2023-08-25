import { useQuery } from "@tanstack/react-query";
import {
    BaseLoadedEntity,
    LoadedEntity,
    combineLoadStates,
    fetchApproversList,
    mapQueryToLoadedEntity,
    useLoadedSubtypes,
} from "react-libs";
import { ItemDataset } from "react-libs/shared-interfaces/RegistryAPI";

export interface UseApproversListOutput {
    // Fetch system approvers id as a list
    approversIdList?: Array<string>;
    // Fetch approvers item info based on their ids
    approversItemList: Array<ItemDataset | undefined>;
    // Store combined status
    response: BaseLoadedEntity;
    // If complete and successfully fetching id list and item list
    complete: boolean;
}

interface UseApproversListProps {
    // onSuccess: () => void;
}

export const useApproversList = (
    props: UseApproversListProps
): UseApproversListOutput => {
    /**
    Hook: useApproversList
    
    Get system approvers list for release approvals
    */

    // Timeout cache after 1 min
    const cacheTimeoutMs = 60000;

    // Fetch approvers list from system
    const fetchSysApproversQuery = useQuery({
        queryKey: ["systemApproversList"],
        queryFn: () => {
            return fetchApproversList();
        },
        staleTime: cacheTimeoutMs,
        refetchOnMount: true,
        enabled: true,
        // onSuccess: props.onSuccess,
    });

    // Fetch other approver's info through id
    const approversIdListData = fetchSysApproversQuery.data;

    const approversItemListRes = useLoadedSubtypes({
        ids: approversIdListData ?? [],
        subtype: "PERSON",
    });

    // Status

    // fetchSysApproversQuery status
    const idListStatus = mapQueryToLoadedEntity(fetchSysApproversQuery);

    // useTypedLoadedItem status
    const approversItemListResult = Array.from(
        approversItemListRes.results.values()
    ) as Array<LoadedEntity<ItemDataset | undefined>>;

    // Get item data
    const approversItemList = approversItemListResult.map(
        (loadEntity) => loadEntity.data
    );

    const itemsStatus = combineLoadStates(approversItemListResult);

    const combinedStatus = combineLoadStates([idListStatus, itemsStatus]);
    // }
    const complete =
        !!combinedStatus &&
        !combinedStatus.error &&
        !combinedStatus.loading &&
        !!approversIdListData &&
        approversIdListData?.length === approversItemListResult.length;

    return {
        approversIdList: approversIdListData,
        approversItemList,
        response: combinedStatus,
        complete,
    };
};
