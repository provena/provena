// Custom hook that manages the react-query/api calls for the "Export" feature. 
import { useState } from "react"
import { useMutation } from "@tanstack/react-query"

import { generateReport } from "react-libs"
import { ItemSubType } from "provena-interfaces/RegistryModels"

export interface useGenerateReportProps {
    // What is the Node ID (either model run or study entity)
    id: string | undefined
    itemSubType: ItemSubType | undefined
    // Chosen depth by the user.
    depth: number
    onSuccess?: (response: any) => void;

}

export const useGenerateReport = (props: useGenerateReportProps) => {

    // Validate that everything is present correctly.
    const requiredItems = [props.id, props.itemSubType, props.depth]
    const dataReady = !requiredItems.some((i) => {
        return i === undefined;
    });

    /* onSuccess is a callback that is fired anytime the query 
       succesfully fetches new data.
     */ 

    // Setting up the useQuery
    const generateReportQuery = useMutation({
        mutationFn: () => {
            console.log({
                node_id: props.id,
                item_subtype: props.itemSubType,
                depth: props.depth
            })
            return generateReport({
                id: props.id!!,
                item_subtype: props.itemSubType!!,
                depth: props.depth

            })
        },
        onSuccess(data){
            if (props.onSuccess !== undefined){
                // If the onSuccess function is defined then calls it
                props.onSuccess(data)
            }
        }
    })

    const submit = () => {
        // Call the mutation function
        generateReportQuery.mutate()

    }

    // Return the values generated in the hook. 

    return {
        dataReady,
        generateReportQuery
    }
}

