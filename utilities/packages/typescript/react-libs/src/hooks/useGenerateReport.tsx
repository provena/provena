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

// Define the return type interface
interface GenerateReportReturn {
  dataReady: boolean;
  error?: unknown;
  isError?: boolean;
  isLoading?: boolean;
  isSuccess?: boolean;
  mutate?: any
  reset?: () => void;
}

export const useGenerateReport = (props: useGenerateReportProps): GenerateReportReturn => {

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
    return {
        dataReady,
        // Spreads out the return of the mutate object.
        ...(dataReady ? generateReportQuery : {})
    }
}
