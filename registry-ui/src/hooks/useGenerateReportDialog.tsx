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
import { useQuery } from "@tanstack/react-query";

import React, { useState } from "react";
import { GenerateReportResponse } from "react-libs/provena-interfaces/ProvenanceAPI";
import { useGenerateReport } from "./useGenerateReport";
import { ItemSubType } from "provena-interfaces/RegistryModels";

export interface GenerateReportProps {
    nodeId: string | undefined;
    itemSubType: ItemSubType | undefined; 
    // This is a wrapper around the other child components and acts as as a callback. 
    onSuccess?: (response: GenerateReportResponse) => void;
}

const DEPTH_LIST = ["1", "2", "3"]

export const useGenerateReportDialog = (props: GenerateReportProps) => {

    const [popUpOpen, setPopupOpen] = useState<boolean>(false);
    const [depth, setDepth] = useState<string>("");

    // Helper functions to open and close the popup. 
    const openDialog = () => {
        setPopupOpen(true);
    }

    const closeDialog = () => {
        // Clear state and close dialog
        setDepth("")
        setPopupOpen(false);

    }

    const handleChange = (event: SelectChangeEvent) => {
        setDepth(event.target.value as string)
    }

    const onSubmit = () => {
        // Validate that a depth has been chosen. 

        if (depth.length !== 0){ 
            // Proceed to submit... 
            if(generateReportHandler.dataReady){ 
                if (generateReportHandler.submit !== undefined){
                    generateReportHandler.submit()
                }
            }

        }

    }

    // Call the react-query defined. 
    const generateReportHandler = useGenerateReport({
        nodeId: props.nodeId, 
        itemSubType: props.itemSubType, 
        depth: depth, 
        onSuccess: (response) => {
            if (props.onSuccess !== undefined){
                props.onSuccess(response)
            }
        }
    })

    // Submit button is disabled if depth is not picked.
    const submitDisabled = depth === ""

    const renderedDialog = (

        <Dialog open={popUpOpen} onClose={closeDialog} fullWidth={true} maxWidth={"md"}>
            <DialogContent>
                <Stack spacing={2} direction="column">

                    Select a depth for the upstream.

                    <FormControl fullWidth>
                        <InputLabel id="depth-select-label">Depth</InputLabel>
                        <Select
                            labelId="depth-select-label"
                            id="depth-simple-select"
                            value={depth}
                            label="Depth"
                            onChange={handleChange}

                        >
                            {DEPTH_LIST.map((item: string) => (
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

                </Stack>
            </DialogContent>
        </Dialog>
    )

    return {
        openDialog,
        renderedDialog
    }

}