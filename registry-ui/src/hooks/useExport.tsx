// Custom hook that manages the react-query/api calls for the "Export" feature. 
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"

export interface UseExportProps {
    // What is the Node ID (either model run or study entity)
    nodeId: string | undefined

    // Chosen depth by the user.
    depth: string
}

export const useExport = (props: UseExportProps) => {

    // Validate that everything is present correctly.
    const requiredItems = [props.nodeId, props.depth]
    const dataReady = !requiredItems.some((i) => {
        return i === undefined;
    });

    // Setting up the useQuery
    const result = useQuery({
        queryKey: ['depth-fetch'],
        queryFn: () => {
            return
        },
        // Setting these values to zero, as the result of this query does not need to be kept.
        cacheTime: 0,
        staleTime: 0 
    })







}

