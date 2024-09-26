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

import React, { useState } from "react";

export interface ExportProps {
    nodeId: string | undefined
}

const DEPTH_LIST = ["1", "2", "3"]

export const useExportDialog = (props: ExportProps) => {

    const { nodeId } = props
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
    }

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