import { useQuery } from "@tanstack/react-query";
import {
    LoadedWithRefetch,
    getJobBySessionId,
    mapQueryToLoadedEntity,
} from "../";
import { JobStatusTable } from "../shared-interfaces/AsyncJobAPI";
import { useState } from "react";

export interface UseJobSessionWatcherProps {
    sessionId?: string;
    enabled?: boolean;
    refetchOnError?: boolean; // default false
    onSuccess?: (data: JobStatusTable) => void;
    adminMode: boolean;
}
export interface UseJobSessionWatcherOutput
    extends LoadedWithRefetch<JobStatusTable | undefined> {
    isAutoRefetching: boolean;
}
export const useJobSessionWatcher = (
    props: UseJobSessionWatcherProps
): UseJobSessionWatcherOutput => {
    /**
    Hook: useJobSessionWatcher

    This hook uses the job API to poll a job until either polling is disabled,
    or the result is successful.
    */

    // Timeout cache after 5s - this acts as polling
    const pollInterval = 2500;
    const dataReady = !!props.sessionId;
    const enabled = props.enabled !== undefined ? props.enabled : dataReady;
    const refetchOnError = props.refetchOnError ?? false;
    const [isAutoRefetching, setIsAutoRefetching] = useState<boolean>(true);
    const fetchQuery = useQuery({
        queryKey: ["fetchjobuser", props.sessionId ?? "noidspecified"],
        queryFn: () => {
            if (props.sessionId === undefined) {
                return Promise.reject(
                    "Can't fetch job info without session id"
                );
            } else {
                return getJobBySessionId({
                    sessionId: props.sessionId!,
                    adminMode: props.adminMode,
                });
            }
        },
        refetchInterval: (data, _) => {
            if (data !== undefined) {
                // Fetch complete
                if (
                    data.job.status === "SUCCEEDED" ||
                    data.job.status === "FAILED"
                ) {
                    // Completed - mark as completed auto refetching
                    setIsAutoRefetching(false);
                    return false;
                } else {
                    // Incomplete
                    if (!isAutoRefetching) {
                        setIsAutoRefetching(true);
                    }
                    return pollInterval;
                }
            } else {
                // Fetch failed - refetch?
                if (refetchOnError) {
                    // Incomplete
                    if (!isAutoRefetching) {
                        setIsAutoRefetching(true);
                    }
                    return pollInterval;
                } else {
                    // Completed - mark as completed auto refetching
                    setIsAutoRefetching(false);
                    return false;
                }
            }
        },
        enabled: enabled,
        onSuccess: (data) => {
            if (props.onSuccess !== undefined) {
                props.onSuccess(data.job);
            }
        },
    });

    return {
        data: fetchQuery.data?.job,
        refetch: fetchQuery.refetch,
        isAutoRefetching: isAutoRefetching,
        ...mapQueryToLoadedEntity(fetchQuery),
    };
};
