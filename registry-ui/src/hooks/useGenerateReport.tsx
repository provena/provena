// Custom hook that manages the react-query/api calls for the "Export" feature. 
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { generateReport } from "react-libs"
import { ItemSubType } from "provena-interfaces/RegistryModels"
import { GenerateReportResponse } from "react-libs/provena-interfaces/ProvenanceAPI"

export interface useGenerateReportProps {
    // What is the Node ID (either model run or study entity)
    nodeId: string | undefined
    itemSubType: ItemSubType | undefined
    // Chosen depth by the user.
    depth: string
    onSuccess?: (response: GenerateReportResponse) => void;

}

export const useGenerateReport = (props: useGenerateReportProps) => {

    // Validate that everything is present correctly.
    const requiredItems = [props.nodeId, props.depth]
    const dataReady = !requiredItems.some((i) => {
        return i === undefined;
    });

    /* onSuccess is a callback that is fired anytime the query 
       succesfully fetches new data.
     */ 

    // Setting up the useQuery
    const generateReportQuery = useQuery<GenerateReportResponse>({
        queryKey: ['depth-fetch'],
        queryFn: () => 
            generateReport({
                node_id: props.nodeId!!, 
                item_subtype: props.itemSubType!!, 
                depth: props.depth

            }), 
        enabled: false,
        onSuccess(data){
            if (props.onSuccess !== undefined){
                // If the onSuccess function is defined then calls it
                props.onSuccess(data)
            }

            
        }
    })

    const submit = () => {

        // Need to manually trigger the query to happen. UseQuery hooks run automatically when the component is rendered
        // but we need the user to select a few things before we render it.
        if (dataReady){
            generateReportQuery.refetch()
        }

    }

    // Return the values generated in the hook. 

    return {
        dataReady, 
        submit: dataReady ? submit : undefined,
        response: dataReady
            ?  {
                data: generateReportQuery.data, 
                loading: generateReportQuery.isLoading, 
                error: generateReportQuery.isError, 
                success: generateReportQuery.isSuccess, 
                fetching: generateReportQuery.isFetching,
                errorMessage: generateReportQuery.error 
                ? (generateReportQuery.error as string)
                : undefined
               }
            
            :undefined
    }
}

