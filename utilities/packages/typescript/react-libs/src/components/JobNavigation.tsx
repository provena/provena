import { Button, Stack } from "@mui/material";
import {
    BATCH_ADMIN_MODE_QSTRING,
    BATCH_ID_QSTRING,
    JOB_BATCH_ROUTE,
    JOB_LIST_ROUTE,
    LIST_ADMIN_MODE_QSTRING,
} from "../";
import { useHistory } from "react-router-dom";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";

export interface JobNavigationComponentProps {
    prevBatchId?: string;
    adminMode: boolean;
}
export const JobNavigationComponent = (props: JobNavigationComponentProps) => {
    /**
    Component: JobNavigationComponent

    Handles providing some basic navigation to top view of job views.

    Back to Job List (always)
    Back to Batch (if navigated from batch ID with qstring)
    */
    const history = useHistory();

    const goToList = (): void => {
        history.push(
            JOB_LIST_ROUTE +
                `?${LIST_ADMIN_MODE_QSTRING}=${props.adminMode.toString()}`
        );
    };

    const goToBatch = (id: string): void => {
        // Open batch view
        history.push(
            JOB_BATCH_ROUTE +
                `?${BATCH_ID_QSTRING}=${id}&${BATCH_ADMIN_MODE_QSTRING}=${props.adminMode.toString()}`
        );
    };

    return (
        <Stack direction="row" justifyContent="flex-start" spacing={2}>
            <Button
                onClick={goToList}
                startIcon={<ArrowBackIcon />}
                variant="outlined"
            >
                Job List
            </Button>
            {!!props.prevBatchId && (
                <Button
                    onClick={() => {
                        goToBatch(props.prevBatchId!);
                    }}
                    startIcon={<ArrowBackIcon />}
                    variant="outlined"
                >
                    Batch Details
                </Button>
            )}
        </Stack>
    );
};
