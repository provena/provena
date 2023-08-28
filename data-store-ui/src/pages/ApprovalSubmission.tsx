import {
    Alert,
    AlertTitle,
    Button,
    Checkbox,
    CircularProgress,
    Dialog,
    FormControl,
    FormControlLabel,
    FormHelperText,
    Grid,
    InputLabel,
    MenuItem,
    Select,
    SelectChangeEvent,
    Stack,
    TextField,
    Theme,
    Typography,
    useTheme,
} from "@mui/material";
import { createStyles, makeStyles } from "@mui/styles";
import { useApprovalSubmit } from "hooks/useApprovalSubmit";
import { useApproversList } from "hooks/useApproversList";
import React, { useEffect, useRef, useState } from "react";
import { useTypedLoadedItem, useUserLinkServiceLookup } from "react-libs";
import {
    ItemBase,
    ItemDataset,
} from "react-libs/shared-interfaces/RegistryAPI";
import { useHistory, useParams } from "react-router-dom";
import { datasetApprovalsTabLinkResolver } from "util/helper";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            padding: theme.spacing(4),
            borderRadius: 5,
            backgroundColor: theme.palette.common.white,
            width: "100%",
            minHeight: "80vh",
        },
        actionButtons: {
            width: "100%",
            justifyContent: "space-around",
        },
        // Success dialog
        successDialog: {
            borderRadius: 5,
            width: "100%",
        },
        // Other useful layout
        fullWidth: { width: "100%" },
        tbPaddings: {
            paddingTop: theme.spacing(2),
            paddingBottom: theme.spacing(2),
        },
    })
);

interface UserDisplayNameProps {
    ownerName?: string;
}

const UserDisplayName = (props: UserDisplayNameProps): JSX.Element => {
    /**
    Component: UserDisplayName
    
    Render user first and last name from owner_name
    */
    const link = useUserLinkServiceLookup({ username: props.ownerName });

    const loadedPerson = useTypedLoadedItem({
        enabled: true,
        id: link.data,
        subtype: "PERSON",
    });

    const typedPerson =
        loadedPerson.data?.item !== undefined
            ? (loadedPerson.data?.item as ItemBase)
            : undefined;

    // parse the display name contents
    const displayName =
        loadedPerson.loading || link.loading
            ? "Loading..."
            : link.error
            ? `An error occurred while loading the approver's user link. Error: ${
                  link.errorMessage ?? "Unknown error..."
              }.`
            : loadedPerson.error
            ? `An error occurred while loading the approver. Error: ${
                  loadedPerson.errorMessage ?? "Unknown error..."
              }.`
            : typedPerson?.display_name ?? "Unknown name";

    return <React.Fragment>{displayName}</React.Fragment>;
};

interface ApprovalSubmissionParams {
    id: string;
}

export const ApprovalSubmission = () => {
    /**
    Component: ApprovalSubmission

    The submission page when admin clicked submit for approval
    */

    const classes = useStyles();
    const theme = useTheme();

    // Dataset id
    const { id: dataset_id } = useParams<ApprovalSubmissionParams>();

    const [approverId, setApproverId] = useState<string>("");

    const [requesterNote, setRequesterNote] = useState<string>("");

    // Record invalid required form input, true for invalid, false for valid
    // For Select
    const [selectInvalidInput, setSelectInvalidInput] =
        useState<boolean>(false);
    // For Checkbox
    const [checkboxInvalidInput, setCheckboxInvalidInput] =
        useState<boolean>(false);

    // Dialog open when submit successfully
    const [successDialogOpen, setSuccessDialogOpen] = useState<boolean>(false);

    // Save dialog timeout timer for cleaning
    const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

    // For redirection
    const history = useHistory();

    // Fetching approvers list

    const approversList = useApproversList({});

    const approversItemList = approversList.approversItemList;

    // use mutate for approval request
    // approverId is checked for undefined before submitting
    const approvalSubmit = useApprovalSubmit();

    // Cleaning
    useEffect(() => {
        return () => handleClean();
    }, []);

    // Error alerts

    // Error when fetching approvers list from system, no further action can be done, return error
    if (!!approversList.response && approversList.response.error) {
        return (
            <Stack direction="column" className={classes.root} spacing={2}>
                <Alert variant="outlined" severity="error">
                    <AlertTitle>
                        Error: An error occurred when fetching the list of
                        approvers.
                    </AlertTitle>
                    {approversList.response.errorMessage ??
                        "Error message is not provided."}
                </Alert>
            </Stack>
        );
    }

    // Handler

    // Checkbox
    const handleCheckboxChange = (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        setCheckboxInvalidInput(!event.target.checked);
    };

    // Approvers list selector
    const handleApproverChange = (event: SelectChangeEvent) => {
        event.preventDefault();
        const selectedApprover = event.target.value as string;

        if (!!selectedApprover && !!dataset_id) {
            setApproverId(selectedApprover);
        }
    };

    // Requester note text field
    const textFieldOnChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        event.preventDefault();
        const requesterNote = event.target.value;
        setRequesterNote(requesterNote);
    };

    // onSuccess
    const handleOnSuccess = () => {
        const delayForRedirect: number = 4000;
        // Open success dialog
        setSuccessDialogOpen(true);
        // Set timer for redirect
        timer.current = setTimeout(() => {
            handleRedirect();
        }, delayForRedirect);
    };

    // Submit
    const handleSubmit = (event: React.SyntheticEvent) => {
        event.preventDefault();

        // Check if input values are valid
        setSelectInvalidInput(!approverId || approverId === "");

        if (!!approverId && approverId !== "") {
            approvalSubmit.mutate(
                {
                    datasetId: dataset_id,
                    approverId: approverId!,
                    requesterNotes: requesterNote,
                },
                { onSuccess: handleOnSuccess }
            );
        }
    };

    // Redirect to dataset's overview tab
    const handleRedirect = () => {
        const desiredLink = datasetApprovalsTabLinkResolver(dataset_id);
        history.push(desiredLink);
    };

    // Cleaning functions before closing
    const handleClean = () => {
        // Clear timer
        if (timer.current) {
            clearTimeout(timer.current);
        }
        // Close dialog window
        setSuccessDialogOpen(false);
    };

    // Status

    const fetchLoading =
        !approversList.response || approversList.response.loading;

    // submitting request
    const isSubmitting = approvalSubmit.isLoading;
    const isSuccess = approvalSubmit.isSuccess;
    const isError = approvalSubmit.isError;

    return (
        <Stack direction="column" className={classes.root} spacing={2}>
            <Typography variant="h4">Submit for Approval</Typography>
            {fetchLoading ? (
                <CircularProgress />
            ) : (
                <form onSubmit={handleSubmit}>
                    <Stack direction="column" spacing={4}>
                        <FormControl fullWidth>
                            {/* Approvers selector */}
                            <Stack>
                                <InputLabel id="demo-simple-select-label">
                                    Approver*
                                </InputLabel>
                                <Select
                                    labelId="approver-select-label"
                                    id="approver-select"
                                    value={approverId}
                                    label="Approver"
                                    onChange={handleApproverChange}
                                    required
                                    error={selectInvalidInput}
                                    disabled={isSubmitting || isSuccess}
                                >
                                    {approversList.complete &&
                                        !!approversItemList &&
                                        approversItemList.length !== 0 &&
                                        approversItemList.map(
                                            (
                                                approverLoadedItem:
                                                    | ItemDataset
                                                    | undefined
                                            ) => (
                                                <MenuItem
                                                    key={approverLoadedItem?.id}
                                                    value={
                                                        approverLoadedItem?.id
                                                    }
                                                >
                                                    <UserDisplayName
                                                        ownerName={
                                                            approverLoadedItem?.owner_username
                                                        }
                                                    />
                                                    {" - "}
                                                    {approverLoadedItem?.id}
                                                </MenuItem>
                                            )
                                        )}
                                </Select>
                                {selectInvalidInput && (
                                    <FormHelperText>
                                        <Typography
                                            variant="inherit"
                                            color={theme.palette.error.main}
                                        >
                                            Please select an approver from the
                                            list to process the approval.
                                        </Typography>
                                    </FormHelperText>
                                )}
                            </Stack>
                        </FormControl>
                        {/* Requester notes */}
                        <Stack>
                            <TextField
                                name="requesterNote"
                                label="Notes to approver"
                                placeholder="Please enter any notes to approver..."
                                multiline
                                fullWidth
                                variant="outlined"
                                rows={12}
                                disabled={isSubmitting || isSuccess}
                                // className={classes.}
                                onChange={textFieldOnChange}
                            />
                        </Stack>
                        {/* Request checkbox */}
                        <Stack
                            direction="column"
                            className={classes.fullWidth}
                            sx={{ alignItems: "start" }}
                        >
                            <FormControlLabel
                                control={
                                    <Checkbox
                                        required
                                        onChange={handleCheckboxChange}
                                        disabled={isSubmitting || isSuccess}
                                    />
                                }
                                label="After you click 'SUBMIT', a request email will be sent to the approver, and the current dataset will be locked. Please ensure that the information you provide is correct before submitting."
                            />
                            {checkboxInvalidInput && (
                                <FormHelperText>
                                    <Typography
                                        variant="inherit"
                                        color={theme.palette.error.main}
                                    >
                                        You must confirm this checkbox to
                                        process the approval request.
                                    </Typography>
                                </FormHelperText>
                            )}
                        </Stack>
                        {/* Action buttons */}
                        <Grid
                            container
                            item
                            xs={12}
                            className={classes.actionButtons}
                        >
                            <Grid item>
                                <Button
                                    variant="contained"
                                    type="button"
                                    onClick={handleRedirect}
                                    disabled={isSubmitting || isSuccess}
                                >
                                    Cancel
                                </Button>
                            </Grid>
                            <Grid item>
                                <Button
                                    variant="contained"
                                    type="submit"
                                    disabled={isSubmitting || isSuccess}
                                >
                                    Submit
                                </Button>
                            </Grid>
                        </Grid>
                    </Stack>
                    {/* Submitting */}
                    {isSubmitting && <CircularProgress />}
                    {/* Success and redirect */}
                    {successDialogOpen && (
                        <Dialog
                            open={successDialogOpen}
                            className={classes.successDialog}
                            fullWidth
                            maxWidth="md"
                        >
                            <Stack
                                direction="column"
                                className={classes.fullWidth}
                                p={4}
                            >
                                <Alert variant="outlined" severity="success">
                                    <AlertTitle>
                                        Success: Your approval request has been
                                        submitted successfully.
                                    </AlertTitle>
                                    You will be redirected to the dataset's
                                    approvals tab in a few seconds...
                                </Alert>
                            </Stack>
                        </Dialog>
                    )}
                    {/* Error */}
                    {isError && (
                        <Stack
                            direction="column"
                            className={`${classes.fullWidth} ${classes.tbPaddings}`}
                        >
                            <Alert variant="outlined" severity="error">
                                <AlertTitle>
                                    Error: An error occurred when submitting the
                                    approval request.
                                </AlertTitle>
                                {approvalSubmit.error ??
                                    "Error message is not provided."}
                            </Alert>
                        </Stack>
                    )}
                </form>
            )}
        </Stack>
    );
};
