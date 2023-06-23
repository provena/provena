import {
    Alert,
    AlertTitle,
    Button,
    CircularProgress,
    Stack,
    Typography,
} from "@mui/material";
import React, { useState } from "react";
import {
    DOCUMENTATION_BASE_URL,
    REGISTRY_LINK,
    useUserLinkServiceLookup,
} from "react-libs";
import { SearchSelectorComponent } from "react-libs";
import { useValidateAndAssignLink } from "../hooks/useValidateAndAssignLink";

interface MissingStatusAlertComponentProps {
    // Is the user in a position where they should link i.e. Registry Write
    // perms
    shouldLink: boolean | undefined;
}
const MissingStatusAlertComponent = (
    props: MissingStatusAlertComponentProps
) => {
    /**
    Component: MissingStatusAlertComponent
    
    Basic failure status for the user link.
    */
    const docLink =
        DOCUMENTATION_BASE_URL +
        "/information-system/getting-started-is/linking-identity.html";

    const content: JSX.Element = (
        <Stack direction="column" spacing={2}>
            <p>
                To register and manage data, entities and provenance in the
                system, you must to register yourself as a Person in the
                Registry and link yourself to this identity. We have detected
                that your account is not linked to a Person.
            </p>
            {!(props.shouldLink ?? true) && (
                <p>
                    However, you are currently a read-only user in the system.
                    You do not need to link your account to a Person if you are
                    only intending to read data in the information system.
                </p>
            )}
            <p>
                For more help, visit our <a href={docLink}>documentation</a>.
            </p>
        </Stack>
    );

    return (
        <Alert severity="warning" variant="outlined">
            <AlertTitle>User is not linked to a Registered Person</AlertTitle>
            {content}
        </Alert>
    );
};

interface SuccessStatusAlertComponentProps {
    personId: string;
}
const SuccessStatusAlertComponent = (
    props: SuccessStatusAlertComponentProps
) => {
    /**
    Component: SuccessStatusAlertComponent

    Basic successful status for the user link.
    */
    const registryLink = REGISTRY_LINK + "/item/" + props.personId;
    const content: JSX.Element = (
        <Stack direction="column" spacing={2}>
            <p>
                Your account is linked to a Person ({props.personId}) in the
                Registry. Click <a href={registryLink}>here</a> to view your
                linked Person in the Registry.
            </p>
        </Stack>
    );

    return (
        <Alert severity="success" variant="outlined">
            <AlertTitle>Your account is linked</AlertTitle>
            {content}
        </Alert>
    );
};

interface RegisterPersonInstructionsComponentProps {}
const RegisterPersonInstructionsComponent = (
    props: RegisterPersonInstructionsComponentProps
) => {
    /**
    Component: RegisterPersonInstructionsComponent

    This is a non interactive guide to the user about registering themselves in
    the Registry.

    */
    const regDeepLink = REGISTRY_LINK + "/registerentity?subtype=PERSON";
    const docLink =
        DOCUMENTATION_BASE_URL + "/getting-started-is/linking-identity.html";

    return (
        <React.Fragment>
            <Typography variant="h6">
                Register yourself as a Person in the Registry
            </Typography>
            <Typography variant="body1">
                Creation and modification of resources in this information
                system are associated with your persistent identity. This
                persistent identity is stored as a Person in the Registry.
                Before proceeding with the following steps, you must register
                yourself as a Person in the Registry. If you already have, you
                can proceed to the next step. Otherwise,{" "}
                <a href={regDeepLink} target="_blank" rel="noreferrer">
                    click here
                </a>{" "}
                to register a Person and return here when you have finished. For
                more help with this process, visit{" "}
                <a href={docLink} rel="noreferrer" target="_blank">
                    our documentation
                </a>
                .
            </Typography>
        </React.Fragment>
    );
};

interface SearchSelectPersonComponentProps {
    personId: string | undefined;
    setPersonId: (id: string | undefined) => void;
}
const SearchSelectPersonComponent = (
    props: SearchSelectPersonComponentProps
) => {
    /**
    Component: SearchSelectPersonComponent
    
    Enables the user to search for and select the registered Person.
    */
    return (
        <React.Fragment>
            <Typography variant="h6">
                Search for yourself in the Registry
            </Typography>
            <Typography variant="body1">
                In the step above, you registered yourself as a Person in the
                Registry. Use the search tool below to select the registered
                Person.
            </Typography>
            {props.personId === undefined && (
                <SearchSelectorComponent
                    selection={props.personId}
                    key="userlinkworkflowsearch"
                    setSelection={props.setPersonId}
                    subtype={"PERSON"}
                    helperText="Select a Person to link your account to"
                />
            )}
        </React.Fragment>
    );
};

interface AlertConfig {
    severity: "info" | "warning" | "error" | "success";
    title: string | JSX.Element;
    body: JSX.Element | null;
}
interface ValidateAssignComponentComponentProps {
    personId: string;
    onAssignment: () => void;
    onClear: () => void;
}
const ValidateAssignComponentComponent = (
    props: ValidateAssignComponentComponentProps
) => {
    /**
    Component: ValidateAssignComponentComponent

    Manages the Person linking validation, submission and result displays
    (including error catches) for the validate/submit workflow.

    Displays as a varying alert depending on status.

    When successful, runs the on assignment callback.

    User can clear from this tool through the on clear callback.
    */
    const assignAndValidate = useValidateAndAssignLink({
        personId: props.personId,
        onAssignmentSuccess: props.onAssignment,
    });

    // Unpack some state from custom hook
    const validationLoading =
        assignAndValidate.validationResult?.loading ?? true;

    const submissionLoading =
        assignAndValidate.submissionResult?.loading ?? false;

    var validationAlertConfig: AlertConfig = {
        severity: "info",
        title: "Please wait...",
        body: <p>Please wait</p>,
    };

    const centeredLoad = (
        <Stack direction="row" justifyContent="center">
            <CircularProgress />
        </Stack>
    );

    // Check states and display suitable alert status

    // Validation in progress
    if (validationLoading) {
        validationAlertConfig = {
            severity: "info",
            title: "Validating selection, please wait...",
            body: centeredLoad,
        };
    }
    // Submission in progress
    else if (submissionLoading) {
        validationAlertConfig = {
            severity: "info",
            title: "Submitting Person assignment, please wait...",
            body: centeredLoad,
        };
    }
    // Submission completed success
    else if (!!assignAndValidate.submissionResult?.success) {
        validationAlertConfig = {
            severity: "success",
            title: "Succesfully linked Person identity",
            body: (
                <p>
                    The selected Person ({props.personId}) was linked to your
                    account. If you need to update or clear this assignment,
                    please contact a system administrator. The page will refresh
                    shortly...
                </p>
            ),
        };
    }
    // Submission completed error
    else if (!!assignAndValidate.submissionResult?.error) {
        validationAlertConfig = {
            severity: "error",
            title: "An error occurred while linking to the specified Person",
            body: (
                <p>
                    An error occurred while linking the selected Person (
                    {props.personId}) to your account. Error details:{" "}
                    {assignAndValidate.submissionResult?.errorMessage ??
                        "Unknown error."}
                    . Please try refreshing and repeating the process. If the
                    issue persists, contact a system administrator.
                </p>
            ),
        };
    }
    // Validation success - awaiting action
    else if (!!assignAndValidate.valid) {
        validationAlertConfig = {
            severity: "success",
            title: "Selected Person is valid for assignment",
            body: (
                <Stack direction="column" spacing={2}>
                    <p>
                        The selected Person is valid for assignment. By
                        selecting "Assign to me" you are specifying that the
                        selected person is you. Actions performed by this
                        account will be linked to this Person. You cannot undo
                        this action.
                    </p>
                    <Stack
                        direction="row"
                        justifyContent="space-between"
                        paddingLeft={1}
                        paddingRight={1}
                        alignItems="center"
                    >
                        {
                            // Clear
                        }
                        <Button
                            variant="outlined"
                            color="warning"
                            onClick={props.onClear}
                        >
                            Clear selection
                        </Button>
                        {
                            // Submit
                        }
                        <Button
                            variant="outlined"
                            color="success"
                            disabled={assignAndValidate.submit === undefined}
                            onClick={assignAndValidate.submit ?? (() => {})}
                        >
                            Assign to me
                        </Button>
                    </Stack>
                </Stack>
            ),
        };
    }
    // Validation failed - report issue
    else if (
        assignAndValidate.valid !== undefined &&
        !assignAndValidate.valid
    ) {
        validationAlertConfig = {
            severity: "error",
            title: "Selected Person is not valid for assignment",
            body: (
                <p>
                    A validation error occurred when verifying this Person as a
                    candidate for assignment. Details:{" "}
                    {assignAndValidate.validationResult?.data?.status.details ??
                        "Unknown."}{" "}
                    Try refreshing and trying the process again. Otherwise,
                    contact an administrator if this error appears incorrect.
                </p>
            ),
        };
    }
    // Validation failed (from API issue i.e. Non 200OK issue)
    else if (!!assignAndValidate.validationResult?.error) {
        validationAlertConfig = {
            severity: "error",
            title: "An error occurred while validating the selection",
            body: (
                <p>
                    An unexpected validation error occurred when verifying this
                    Person as a candidate for assignment. Details:{" "}
                    {assignAndValidate.validationResult?.errorMessage ??
                        "Unknown error."}{" "}
                    Try refreshing and trying the process again. Otherwise,
                    contact an administrator if this error appears incorrect.
                </p>
            ),
        };
    }

    const currentAlert = (
        <Alert
            severity={validationAlertConfig.severity}
            variant="outlined"
            // Force max width
            style={{ width: "100%" }}
        >
            <Stack direction="column" spacing={2} justifyContent="flex-start">
                <AlertTitle>{validationAlertConfig.title}</AlertTitle>
                {validationAlertConfig.body}
            </Stack>
        </Alert>
    );

    return (
        <Stack direction="column" spacing={1}>
            <Typography variant="h6">
                Assign selected Person ({props.personId})
            </Typography>
            {
                // validation section
            }
            {currentAlert}
        </Stack>
    );
};

export interface UserLinkWorkflowComponentProps {}
export const UserLinkWorkflowComponent = (
    props: UserLinkWorkflowComponentProps
) => {
    /**
    Component: UserLinkWorkflowComponent
    
    Manages the username <-> person link process. 

    Guide to process for user.
    */

    // Get the current status
    const link = useUserLinkServiceLookup({});
    const shouldLink = link.shouldLink;
    const linked = !!link.data;

    // Determine top status section
    const statusSection: JSX.Element = (
        <React.Fragment>
            <Typography variant="h6">Link Status</Typography>
            {linked ? (
                <SuccessStatusAlertComponent personId={link.data!} />
            ) : (
                <MissingStatusAlertComponent shouldLink={shouldLink} />
            )}
        </React.Fragment>
    );

    // Should the lower instructional sections be shown?
    const showInstructionalSections = !linked;

    // State for instructional parts
    const [personId, setPersonId] = useState<string | undefined>(undefined);

    // Show checks

    // Show search as long as no link is present
    const showSearch = showInstructionalSections;

    // Show instructions as long as no link is present
    const showInstructions = showInstructionalSections;

    // Show validate and submit tool as long as no link present and person
    // selected
    const showValidateAssign =
        showInstructionalSections && personId !== undefined;

    // Wait 3 seconds before force refreshing upon assignment
    const refreshDelayOnSuccess = 6000;

    return (
        <Stack direction="column" spacing={2}>
            {link.loading ? (
                <CircularProgress />
            ) : link.error ? (
                <Alert variant="outlined" severity="error">
                    <AlertTitle>Could not retrieve link status</AlertTitle>An
                    error occurred while determining the link status. Error
                    message: {link.errorMessage ?? "Unknown"}. Try refreshing
                    the page. If the error persists, contact an adminstrator.
                </Alert>
            ) : (
                <React.Fragment>
                    {statusSection}
                    {showInstructions && (
                        <RegisterPersonInstructionsComponent />
                    )}
                    {showSearch && (
                        <SearchSelectPersonComponent
                            personId={personId}
                            setPersonId={setPersonId}
                        />
                    )}
                    {showValidateAssign && (
                        <ValidateAssignComponentComponent
                            personId={personId}
                            onClear={() => {
                                setPersonId(undefined);
                            }}
                            onAssignment={() => {
                                setTimeout(() => {
                                    link.refetch();
                                }, refreshDelayOnSuccess);
                            }}
                        />
                    )}
                </React.Fragment>
            )}
        </Stack>
    );
};
