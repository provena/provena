import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { Button, Stack, Typography } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useMutation } from "@tanstack/react-query";
import React, { useState } from "react";
import { adminLaunchJob } from "../";
import { JobSubType, JobType } from "../shared-interfaces/AsyncJobModels";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        wakerBox: {
            background: theme.palette.grey[100],
            borderRadius: "8px",
            padding: "25px",
            border: "1px solid #999",
            maxWidth: "50vw",
        },
    })
);

const JOB_TYPE_WAKE_UP_MAP: Map<JobType, JobSubType> = new Map([
    ["EMAIL", "EMAIL_WAKE_UP"],
    ["REGISTRY", "REGISTRY_WAKE_UP"],
    ["PROV_LODGE", "PROV_LODGE_WAKE_UP"],
]);

interface PerformWakeupInputs {
    jobType: JobType;
    jobSubType: JobSubType;
}
interface UsePerformWakeupProps {}
const usePerformWakeup = (props: UsePerformWakeupProps) => {
    /**
    Hook: usePerformWakeup

    React query mutation to perform a wakeup up 
    */
    return useMutation({
        mutationFn: (inputs: PerformWakeupInputs) => {
            return adminLaunchJob({
                request: {
                    job_payload: {},
                    job_sub_type: inputs.jobSubType,
                    job_type: inputs.jobType,
                },
            });
        },
    });
};

interface WakeUpComponentProps {
    jobType: JobType;
    jobSubType: JobSubType;
}

const WakeUpComponent = (props: WakeUpComponentProps) => {
    /**
    Component: WakeUpComponent

    Displays/performs a wake up operation 
    */

    const wakeUpOp = usePerformWakeup({});
    // Is the mutation in progress
    const inProgress = wakeUpOp.isLoading;

    const [showingSuccess, setShowingSuccess] = useState<boolean>(false);
    const [showingError, setShowingError] = useState<boolean>(false);

    return (
        <Stack direction="row" justifyItems="flex-start" spacing={1.5}>
            <Button
                variant="outlined"
                onClick={() => {
                    wakeUpOp.mutate(
                        {
                            ...props,
                        },
                        {
                            onSuccess: () => {
                                // Show success temporarily
                                setShowingSuccess(true);
                                setTimeout(() => {
                                    setShowingSuccess(false);
                                }, 2500);
                            },
                            onError: () => {
                                // Show error temporarily
                                setShowingError(true);
                                setTimeout(() => {
                                    setShowingError(false);
                                }, 10000);
                            },
                        }
                    );
                }}
                disabled={inProgress || showingSuccess || showingError}
            >
                Wake Up
            </Button>
            <p>Wake up {props.jobType}</p>
            {showingSuccess && <CheckCircleIcon color="success" />}
            {showingError && (
                <React.Fragment>
                    <CancelIcon color="error" />
                    <p>
                        Error:{" "}
                        {wakeUpOp.error ?? "None provided. Check console."}
                    </p>
                </React.Fragment>
            )}
        </Stack>
    );
};

export interface JobWakerComponentProps {}
export const JobWakerComponent = (props: JobWakerComponentProps) => {
    /**
    Component: JobWakerComponent

    Enables an admin user to wake up any of a set of job types.
    
    */
    const classes = useStyles();
    return (
        <Stack className={classes.wakerBox} spacing={2}>
            <Typography variant="h6">Job Waker</Typography>
            <Stack spacing={1.5}>
                {Array.from(JOB_TYPE_WAKE_UP_MAP.entries()).map(
                    ([type, subType]) => {
                        return (
                            <WakeUpComponent
                                jobType={type}
                                jobSubType={subType}
                            ></WakeUpComponent>
                        );
                    }
                )}
            </Stack>
        </Stack>
    );
};
