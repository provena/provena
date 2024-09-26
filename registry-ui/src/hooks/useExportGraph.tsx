import { useState } from "react";

export const useExportDialog = () => {

    const [popUpOpen, setPopupOpen] = useState<boolean>(false);

    // Helper functions to open and close the popup. 
    const openDialog = () => {
        setPopupOpen(true);
    }

    const closeDialog = () => {
        setPopupOpen(false);

    }

    return {
        popUpOpen,
        openDialog,
        closeDialog
    }

}