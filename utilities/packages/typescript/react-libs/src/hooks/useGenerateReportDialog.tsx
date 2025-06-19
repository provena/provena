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

// A literal list with set depth values.
const DEPTH_LIST = [1,2,3]

export const useGenerateReportDialog = (props: GenerateReportProps) => {

    const [popUpOpen, setPopupOpen] = useState<boolean>(false);
    const [depth, setDepth] = useState<number>(DEPTH_LIST[0]);
    
    // Call the react-query defined. 
    const {mutate, dataReady} = useGenerateReport({
        id: props.id, 
        itemSubType: props.itemSubType, 
        depth: depth
    })

    // Helper functions to open and close the popup. 
    const openDialog = () => {
        setPopupOpen(true);
    }

    const closeDialog = () => {
        // Clear state and close dialog
        setDepth(DEPTH_LIST[0])
        setPopupOpen(false);
        
        if(dataReady){
            // reset mutation
            mutate?.reset()
        }
    }

    const handleChange = (event: SelectChangeEvent) => {
        setDepth(parseInt(event.target.value))
    }

    const onSubmit = () => {
        // Validate that a depth has been chosen.
        if (depth !== null && dataReady){ 
            // Proceed to submit... 
            mutate?.mutate()
        }
    }

    // Submit button is disabled if depth is not picked.
    const submitDisabled = depth === null

    const renderedDialog = (
        <Dialog open={popUpOpen} onClose={closeDialog} fullWidth={true} maxWidth={"md"}>
            <DialogContent>
                <Stack spacing={2} gap={2} direction="column">

                    {mutate?.isError && (
                        <Alert severity="error" variant="outlined">
                        <AlertTitle>An error occurred</AlertTitle>
                        <Typography variant="subtitle1">
                            An error occurred while running the Generate Report operation. Error:{" "}
                            {mutate?.error
                            ? stripPossibleFullStop(mutate?.error as string)
                            : "Unknown. Try refreshing the page and performing the operation again, or contact an administrator for assistance."}
                        </Typography>
                        </Alert>
                    )}

                    {mutate?.isSuccess && (
                        <Alert severity="success" variant="outlined">
                            <AlertTitle>Your file was downloaded successfully.</AlertTitle>
                        </Alert>
                    )}

                    {!mutate?.isSuccess && (
                        <>   
                        <DialogContentText>
                                Generate a word document containing the associated inputs, model runs and outputs
                                originating from this {props.itemSubType} upto your chosen upstream depth and a fixed
                                downstream depth of 1.
                            </DialogContentText>
                            <FormControl fullWidth>
                                <InputLabel id="depth-select-label">Depth</InputLabel>
                                <Select
                                    labelId="depth-select-label"
                                    id="depth-simple-select"
                                    value = {String(depth)}
                                    label="Depth"
                                    onChange={handleChange}

                                >
                                    {DEPTH_LIST.map((item: number) => (
                                        <MenuItem value={item} key={item}> {item}</MenuItem>
                                    ))}
                                </Select>
                                <Typography variant="caption" color="textSecondary">
                                    Select depth level for upstream exploration.
                                </Typography>
                            </FormControl>
                        </>
                    )}
                </Stack>
                <DialogActions>
                    <Button
                        onClick={closeDialog}
                    >
                        {mutate?.isSuccess? "Close" : "Cancel"}
                    </Button>
                    {!mutate?.isSuccess && (
                    <Button
                        color="success"
                        disabled={submitDisabled}
                        onClick={onSubmit}
                    >
                        {mutate?.isLoading ? "Generating..." : "Generate Report"}
                    </Button>
                    )}
                </DialogActions>
            </DialogContent>
        </Dialog>
    )

    return {
        openDialog,
        closeDialog,
        renderedDialog
    }

}