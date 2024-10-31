import {
    Alert,
    AlertTitle,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Stack,
    Typography,
    MenuItem,
    FormControl,
    Select,
    InputLabel,
    SelectChangeEvent
} from "@mui/material";

import { useState } from "react";
import { useGenerateReport } from "./useGenerateReport";
import { ItemSubType } from "../provena-interfaces/RegistryModels";
import { stripPossibleFullStop } from "../util";

export interface GenerateReportProps {
    id: string | undefined;
    itemSubType: ItemSubType | undefined; 
}

const DEPTH_LIST = [1,2,3]

export const useGenerateReportDialog = (props: GenerateReportProps) => {

    const [popUpOpen, setPopupOpen] = useState<boolean>(false);
    const [depth, setDepth] = useState<number | null>(null);
    
    // Call the react-query defined. 
    const {mutate, isError, reset, isLoading, isSuccess, error, data, dataReady} = useGenerateReport({
        id: props.id, 
        itemSubType: props.itemSubType, 
        depth: depth!, 
        onSuccess: () => {
            //
        },
        onError:(error) => {
            //
        }
    })

    // Helper functions to open and close the popup. 
    const openDialog = () => {
        setPopupOpen(true);
    }

    const closeDialog = () => {
        // Clear state and close dialog
        setDepth(null)
        setPopupOpen(false);
        // reset mutation
        reset();
    }

    const handleChange = (event: SelectChangeEvent) => {
        setDepth(parseInt(event.target.value))
    }

    const onSubmit = () => {
        // Validate that a depth has been chosen.
        if (depth !== null && dataReady){ 
            // Proceed to submit... 
            mutate();
        }
    }

    // Submit button is disabled if depth is not picked.
    const submitDisabled = depth === null

    const renderedDialog = (

        <Dialog open={popUpOpen} onClose={closeDialog} fullWidth={true} maxWidth={"md"}>
            <DialogContent>
                <Stack spacing={2} direction="column">
                    Select a depth for the upstream.
                    
                    {isError && (
                        <Alert severity="error" variant="outlined">
                        <AlertTitle>An error occurred</AlertTitle>
                        <Typography variant="subtitle1">
                            An error occurred while running the link operation. Error:{" "}
                            {error
                            ? stripPossibleFullStop(error as string)
                            : "Unknown"}
                            . Try refreshing the page and performing the operation
                            again, or contact an administrator for assistance.
                        </Typography>
                        </Alert>
                    )}

                    {isSuccess && (

                        <Alert severity="success" variant="outlined">
                            <AlertTitle>Your file was downloaded successfully.</AlertTitle>
                        </Alert>
                    
                    )}

                    {!isSuccess && (
                        <>

                        <FormControl fullWidth>
                            <InputLabel id="depth-select-label">Depth</InputLabel>
                            <Select
                                labelId="depth-select-label"
                                id="depth-simple-select"
                                label="Depth"
                                onChange={handleChange}

                            >
                                {DEPTH_LIST.map((item: number) => (
                                    <MenuItem value={item} key={item}> {item}</MenuItem>
                                ))}

                            </Select>

                        </FormControl>

                        <DialogActions>
                            <Button
                                onClick={closeDialog}
                            >
                                Cancel
                            </Button>
                            <Button
                                color="success"
                                disabled={submitDisabled}
                                onClick={onSubmit}
                            >
                                Submit
                            </Button>
                        </DialogActions>
                        </>
                    )}

                </Stack>
            </DialogContent>
        </Dialog>
    )

    return {
        openDialog,
        closeDialog,
        renderedDialog
    }

}