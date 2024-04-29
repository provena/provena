import { useRef, useState } from "react";
import {
  BaseLoadedEntity,
  LoadedEntity,
  combineLoadStates,
  fetchBySubtype,
  mapQueryToLoadedEntity,
} from "../";
import { ItemBase } from "../provena-interfaces/RegistryModels";
import { useQueries } from "@tanstack/react-query";
import { GenericFetchResponse } from "../provena-interfaces/RegistryAPI";
export interface UseLoadedVersionListProps {
  // What is the starting item?
  startingItem: ItemBase;
}
export interface VersionListEntry {
  id: string;
}

export interface UseLoadedVersionListOutput extends BaseLoadedEntity {
  items: Array<LoadedEntity<ItemBase>>;
  // Complete not means successful, only means the start item and final item is fetched
  complete: boolean;
  // Record starting item's index in the final output. Start with 0
  startingIndex: number;
}
export const useLoadedVersionList = (
  props: UseLoadedVersionListProps,
): UseLoadedVersionListOutput => {
  /**
    Hook: useLoadedVersionList

    Manages the fetching of a complete lineage forwards and back based on a starting item.

    Ensure consuming component keyed by starting id to force remount!
    */

  const item = props.startingItem;
  const subtype = item.item_subtype;

  // Manage a list of fetched entities
  const [fetchedVersionList, setFetchedVersionList] = useState<
    Array<VersionListEntry>
  >([
    {
      id: item.id,
    },
  ]);

  // Count starting item's index in final return list, start with 0
  const startingIndex = useRef<number>(0);

  const pushOrPrependItem = (id: string, pre: boolean) => {
    setFetchedVersionList((oldList: Array<VersionListEntry>) => {
      const newList: Array<VersionListEntry> = JSON.parse(
        JSON.stringify(oldList),
      );
      if (pre) {
        newList.unshift({ id });
        startingIndex.current++;
      } else {
        newList.push({ id });
      }

      return newList;
    });
  };

  const cacheTime = 30 * 1000; // 30 seconds
  type QueryRefetchType = "always";

  const versionsQueryData = useQueries({
    queries: fetchedVersionList.map((versionEntry, index) => {
      return {
        queryKey: ["versionitemfetch", versionEntry.id],
        queryFn: () => {
          // Fetch by the subtype and id - don't allow seeds!
          return fetchBySubtype(versionEntry.id, subtype, false);
        },
        staleTime: cacheTime,
        // Pointless cast to please typescript gods
        refetchOnMount: "always" as QueryRefetchType,
        // When successful query, possibly update resolved id list to fetch next step
        onSuccess: (data: GenericFetchResponse) => {
          // If we are at start/end then we proceed

          if (!data.status.success) {
            // Something went wrong - nothing can be done
            return;
          }

          if (!data.item) {
            // Item isn't present - nothing can be done
            return;
          }

          if (!data.item.versioning_info) {
            // Item, for some reason, has no versioning info!
            return;
          }

          // Pull out versioning info
          const vinfo = data.item.versioning_info;

          // Go back if we are at start (oldest)
          const goBack = index === 0;

          // Go forwards if we are at end (latest)
          const goForwards = index === fetchedVersionList.length - 1;

          if (goBack && !!vinfo.previous_version) {
            // We are at the start and have previous version!
            pushOrPrependItem(
              vinfo.previous_version,
              // Prepend
              true,
            );
          }
          if (goForwards && !!vinfo.next_version) {
            // We are at the start and have previous version!
            pushOrPrependItem(
              vinfo.next_version,
              // Postpend
              false,
            );
          }
        },
      };
    }),
  });

  const mappedQueries = versionsQueryData.map((q) => {
    return {
      // Cast to ItemBase - definitely item as seeds are disabled
      data: q.data?.item !== undefined ? (q.data.item as ItemBase) : undefined,
      ...mapQueryToLoadedEntity(q),
    };
  });
  const combinedState = combineLoadStates(mappedQueries);

  const complete =
    !!mappedQueries[0].data?.versioning_info &&
    mappedQueries[0].data?.versioning_info?.previous_version === null &&
    !!mappedQueries[mappedQueries.length - 1].data?.versioning_info &&
    mappedQueries[mappedQueries.length - 1].data?.versioning_info
      ?.next_version === null;

  const response = {
    ...combinedState,
    items: mappedQueries,
    complete,
    startingIndex: startingIndex.current,
  };

  return response;
};
