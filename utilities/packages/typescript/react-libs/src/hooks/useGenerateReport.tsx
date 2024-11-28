// A small custom hook that manages the react-query/api calls for the "Export" feature. 
import { useMutation} from "@tanstack/react-query"

import { generateReport } from "../queries"
import { ItemSubType } from "../provena-interfaces/RegistryModels"

export interface useGenerateReportProps {
    // What is the Node ID (either model run or study entity)
    id: string | undefined
    itemSubType: ItemSubType | undefined
    // Chosen depth by the user.
    depth: number
}
export const useGenerateReport = (props: useGenerateReportProps) => {

    // Validate that everything is present correctly.
    const requiredItems = [props.id, props.itemSubType, props.depth]
    const dataReady = !requiredItems.some((i) => {
        return i === undefined;
    });

    // Setting up the useQuery
    const generateReportQuery = useMutation({
        mutationFn: () => {
            return generateReport({
                id: props.id!!,
                item_subtype: props.itemSubType!!,
                depth: props.depth

            })
        }
    })

    // Return the values generated in the hook. 
    return {dataReady:dataReady, mutate: dataReady ? generateReportQuery: undefined}

}
