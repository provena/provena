import { useEffect, useState } from "react";
import { ItemBase } from "../shared-interfaces/RegistryModels";
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Stack,
} from "@mui/material";
import { VersionsDataGridSelectorComponent } from "../components/VersionsDataGridSelector";
import { useQueryStringVariable } from "./queryStringVariable";

export interface UseVersionSelectorProps {
    // The item to analyse for historical options
    item?: ItemBase;
}
export interface UseVersionSelectorOutput {
    state?: {
        historyId?: number;
    };
    controls?: {
        startSelection: () => void;
        manuallySetId: (id: number | undefined) => void;
    };
    render: () => JSX.Element | null;
}
export const useVersionSelector = (
    props: UseVersionSelectorProps
): UseVersionSelectorOutput => {
    /**
    Hook: useVersionSelector

    Manages the state required and the rendering of a popup which selects the
    version of an item's history.

    Returns a render method which is always accurate to the state of the
    selection process.
    */

    // State contains the status of popup and the history id
    const { value: historyIdStr, setValue: setHistoryId } =
        useQueryStringVariable({ queryStringKey: "version" });
    const historyId = historyIdStr ? Number(historyIdStr) : undefined;
    const [tempSelectionState, setTempSelectionState] = useState<
        number | undefined
    >(undefined);
    const [popupOpen, setPopupOpen] = useState<boolean>(false);

    // Whenever the popup is opened, reset the selection state to either
    // undefined or the current history ID if defined
    useEffect(() => {
        if (popupOpen && props.item !== undefined) {
            setTempSelectionState(historyId ?? undefined);
        }
    }, [popupOpen]);

    // If the input item is undefined (e.g. loading), then return nothing and a null render
    if (props.item === undefined) {
        return {
            render: () => {
                return null;
            },
        };
    }

    // Otherwise - check if we need to render the selector
    var render: () => JSX.Element | null = () => {
        return null;
    };

    if (popupOpen) {
        render = () => {
            return (
                <Dialog
                    open={popupOpen}
                    onClose={() => {
                        setPopupOpen(false);
                    }}
                    fullWidth={true}
                    maxWidth={"md"}
                >
                    <DialogTitle>Version Selector</DialogTitle>
                    <DialogContent>
                        <Stack spacing={2}>
                            <DialogContentText>
                                Please choose a version from the below list.
                            </DialogContentText>
                            <VersionsDataGridSelectorComponent
                                // The item is certainly defined at this point
                                history={props.item!.history}
                                currentId={historyId}
                                selected={tempSelectionState}
                                setSelectedId={setTempSelectionState}
                            />
                        </Stack>
                    </DialogContent>
                    <DialogActions>
                        <Button
                            onClick={() => {
                                setPopupOpen(false);
                            }}
                        >
                            Cancel
                        </Button>
                        <Button
                            color="success"
                            disabled={tempSelectionState === undefined}
                            onClick={() => {
                                if (tempSelectionState !== undefined) {
                                    if (setHistoryId !== undefined) {
                                        setHistoryId(
                                            tempSelectionState.toString()
                                        );
                                    } else {
                                        console.error(
                                            "Unexpected undefined history ID query string update function. No action taken on submission. Contact administrator."
                                        );
                                    }
                                    setPopupOpen(false);
                                }
                            }}
                        >
                            Submit
                        </Button>
                    </DialogActions>
                </Dialog>
            );
        };
    }

    // return the controls and state
    return {
        render,
        state: {
            historyId: historyId,
        },
        controls: {
            startSelection: () => {
                setPopupOpen(true);
            },
            manuallySetId: (id) => {
                if (setHistoryId !== undefined) {
                    setHistoryId(id ? id.toString() : undefined);
                }
            },
        },
    };
};
