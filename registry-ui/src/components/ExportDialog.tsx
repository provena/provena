// A custom hook to render the pop up of selecting your upstream depth. 
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
} from "@mui/material";

import { useExportDialog } from "hooks/useExportGraph";

export interface ExportProps {
    nodeId: string | undefined
    popUpOpen: boolean
    closeDialog: () => void
}

export const ExportDialogComponent = (props: ExportProps) => {

    const { nodeId, popUpOpen, closeDialog } = props;

    return (

        <Dialog open={popUpOpen} onClose={closeDialog}>

            <DialogContent>

                Hello, my node ID is `${nodeId}`

            </DialogContent>


        </Dialog>

    )


}