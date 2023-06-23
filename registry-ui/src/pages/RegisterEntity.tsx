import {
    Alert,
    AlertTitle,
    Button,
    CircularProgress,
    Grid,
    Stack,
    TextField,
    Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { useKeycloak } from "@react-keycloak/web";
import Form from "@rjsf/mui";
import { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { observer } from "mobx-react-lite";
import { useEffect, useState } from "react";
import {
    AutoCompleteDatasetTemplateLookup,
    AutoCompleteModelLookup,
    AutoCompleteModelRunWorkflowDefinitionLookup,
    AutoCompleteOrcid,
    AutoCompleteOrganisationLookup,
    AutoCompletePersonLookup,
    AutoCompletePublisher,
    DATA_STORE_LINK,
    LoadedEntity,
    PROV_STORE_LINK,
    combineLoadStates,
    mapSubTypeToPrettyName,
    startsWithVowel,
    useAccessCheck,
    useQueryStringVariable,
    useTypedQueryStringVariable,
    useUserLinkEnforcer,
    userLinkEnforcerDocumentationLink,
    userLinkEnforcerProfileLink,
} from "react-libs";
import { PersonEthicsTickConsent } from "../components/ConsentTickBoxOverrides";
import DatasetTemplateAdditionalAnnotationsOverride from "../components/DatasetTemplateAdditionalAnnotationsOverride";
import { ItemSubtypeSelector } from "../components/ItemSubtypeSelector";
import WorkflowDefinitionAutomationScheduleOverride from "../components/WorkflowDefinitionAutomationScheduleOverride";
import WorkflowTemplateAnnotationsOverride from "../components/WorkflowTemplateAnnotationsOverride";
import { registerableEntityTypes } from "../entityLists";
import { useCreateItem } from "../hooks/useCreateItem";
import { useFormSetup } from "../hooks/useFormSetup";
import { useUpdateItem } from "../hooks/useUpdateItem";
import { ItemSubType } from "../shared-interfaces/RegistryAPI";
import {
    DomainInfoBase,
    PersonDomainInfo,
} from "../shared-interfaces/RegistryModels";
import { getRegisteringDocumentationLink } from "../util/helper";
import lodashSet from "lodash.set";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        stackContainer: {
            backgroundColor: "white",
            borderRadius: 5,
            paddingLeft: theme.spacing(4),
            paddingRight: theme.spacing(4),
            paddingTop: theme.spacing(2),
            paddingBottom: theme.spacing(2),
        },
        interactionContainer: {
            paddingTop: theme.spacing(2),
            paddingLeft: theme.spacing(1),
        },
        interactionPanel: {
            display: "flex",
            justifyContent: "space-around",
            alignItems: "center",
            backgroundColor: "white",
            padding: theme.spacing(2),
            borderRadius: 5,
        },
        mainActionButton: {
            marginBottom: theme.spacing(2),
            width: "40%",
        },
    })
);

export const subtypeQStringKey = "subtype";

const customFields: { [name: string]: any } = {
    autoCompleteOrcid: AutoCompleteOrcid,
    autoCompleteDatasetTemplateLookup: AutoCompleteDatasetTemplateLookup,
    autoCompleteModelLookup: AutoCompleteModelLookup,
    autoCompleteModelRunWorkflowDefinitionLookup:
        AutoCompleteModelRunWorkflowDefinitionLookup,
    autoCompletePersonLookup: AutoCompletePersonLookup,
    autoCompleteOrganisationLookup: AutoCompleteOrganisationLookup,
    autoCompleteRORLookup: AutoCompletePublisher,
    datasetTemplateMetadataOverride:
        DatasetTemplateAdditionalAnnotationsOverride,
    personEthicsTickBox: PersonEthicsTickConsent,
};

const customWidgets: { [name: string]: any } = {
    workflowDefinitionAutomationScheduleOverride:
        WorkflowDefinitionAutomationScheduleOverride,
    annotationsOverride: WorkflowTemplateAnnotationsOverride,
};

export interface AutofillFuncInputs {
    // Can expand this later as more info is available
    tokenParsed: { [k: string]: any };
    // Update func to set data
    setFormData: (formData: any) => void;
}

type AutofillFunc = (inputs: AutofillFuncInputs) => void;

// Auto fills - these are optional and allow for auto filling when schema
// loaded - create only
const autofills: Map<ItemSubType, AutofillFunc> = new Map([
    [
        "PERSON",
        (inputs: AutofillFuncInputs) => {
            const firstName = inputs.tokenParsed.given_name ?? "";
            const lastName = inputs.tokenParsed.family_name ?? "";
            const email = inputs.tokenParsed.email ?? "";

            inputs.setFormData({
                display_name: `${firstName} ${lastName}`,
                email: email,
                first_name: firstName,
                last_name: lastName,
            } as PersonDomainInfo);
        },
    ],
]);

interface RedirectConfiguration {
    url: string;
    description: string;
}

const subtypeRedirects: Map<ItemSubType, RedirectConfiguration> = new Map([
    [
        "DATASET",
        {
            url: DATA_STORE_LINK + "/new_dataset",
            description: "To register a Dataset, visit the Data Store.",
        },
    ],
    [
        "MODEL_RUN",
        {
            url: PROV_STORE_LINK,
            description:
                "To register a Model Run, you can use the Provenance Store.",
        },
    ],
]);

interface DisplayRedirectProps {
    config: RedirectConfiguration;
}
const DisplayRedirect = observer((props: DisplayRedirectProps) => {
    /**
    Component: DisplayRedirect

    Displays helpful message to visit appropriate location to register non
    directly registerable type.
    */
    const classes = useStyles();
    const desc = props.config.description;
    const link = props.config.url;
    return (
        <div style={{ width: "100%" }} className={classes.stackContainer}>
            <Grid item>
                <Typography variant="h6">
                    You cannot register this type of entity in the Registry
                </Typography>
                <Typography variant="subtitle1">
                    {desc} You can <a href={link}>click here</a> to register an
                    entity of this type.
                </Typography>
            </Grid>
        </div>
    );
});

interface DocumentationLinkDisplayProps {
    itemSubtype: ItemSubType;
    verb?: string;
}
const DocumentationLinkDisplay = (props: DocumentationLinkDisplayProps) => {
    /**
        Component: DocumentationLinkDisplay

        Provides a link to the documentation depending on the currently selected
        item subtype - simple p tag response - no styling
    */
    const classes = useStyles();
    const docLink = getRegisteringDocumentationLink(props.itemSubtype);
    return (
        <p>
            For help {props.verb ? props.verb : "registering"} a{" "}
            {mapSubTypeToPrettyName(props.itemSubtype)} visit{" "}
            {docLink ? (
                <a href={docLink} target="_blank">
                    our documentation
                </a>
            ) : (
                <p>our documentation</p>
            )}
            .
        </p>
    );
};

interface HeaderBoxComponentProps {
    isEditMode: boolean;
    subtype: ItemSubType;

    // Is the user linked - this is used to insert a warning for People
    linked: boolean;
}
const HeaderBoxComponent = (props: HeaderBoxComponentProps) => {
    /**
    Component: HeaderBoxComponent
    Contains the "Registering/Editing" header info in a box.

    Simple MUI title and subtitle inside div
    */
    const classes = useStyles();
    const displayName = mapSubTypeToPrettyName(props.subtype);
    return (
        <div>
            <Typography variant="h4">
                {(props.isEditMode ? "Editing" : "Registering") +
                    (startsWithVowel(displayName) ? " an " : " a ") +
                    displayName}
            </Typography>
            <Typography variant="subtitle1">
                <DocumentationLinkDisplay
                    itemSubtype={props.subtype}
                    verb={props.isEditMode ? "editing" : "registering"}
                ></DocumentationLinkDisplay>
            </Typography>
            {props.subtype === "PERSON" && props.linked && (
                <div style={{ width: "100%" }}>
                    <Alert variant="outlined" severity="warning">
                        <AlertTitle>
                            Are you sure you want to register a Person?
                        </AlertTitle>
                        Our system has detected that your user account is
                        already linked to a Person in the Registry. Are you sure
                        you want to create another Person in the Registry? We do
                        not recommend that you register a Person on behalf of
                        another user. Please contact us if you are uncertain.
                    </Alert>
                </div>
            )}
        </div>
    );
};

interface ReasonInputComponentProps {
    reason: string;
    setReason: (reason: string) => void;
}
const ReasonInputComponent = (props: ReasonInputComponentProps) => {
    /**
    Component: ReasonInputComponent
    Provides a wrapper around the reason when updating
    */
    const classes = useStyles();
    return (
        <div className={classes.stackContainer}>
            <Stack direction="column" spacing={2}>
                <Typography variant="subtitle1">
                    Please provide an explanation for why this update is
                    required*
                </Typography>
                <TextField
                    fullWidth
                    placeholder={"Why are you updating this item?"}
                    required={true}
                    multiline
                    value={props.reason}
                    onChange={(e) => {
                        props.setReason(e.target.value);
                    }}
                />
            </Stack>
        </div>
    );
};

interface CreateItemResultDisplayComponentProps {
    createHook: ReturnType<typeof useCreateItem>;
}
const CreateItemResultDisplayComponent = (
    props: CreateItemResultDisplayComponentProps
) => {
    /**
    Component: CreateItemResultDisplayComponent
    
    Displays the results of creating an item.
    */
    const classes = useStyles();
    const status = props.createHook.response;
    var content: JSX.Element = <p></p>;
    if (status?.loading) {
        content = (
            <Stack direction="column" justifyContent="center">
                <Stack
                    direction="row"
                    spacing={2}
                    alignItems="center"
                    justifyContent="center"
                >
                    <Typography variant="subtitle1">
                        Submitting...please wait
                    </Typography>
                    <CircularProgress />
                </Stack>
            </Stack>
        );
    } else if (
        status?.error ||
        status === undefined ||
        status?.data === undefined
    ) {
        content = (
            <Alert severity={"error"}>
                <AlertTitle>Error</AlertTitle>
                <p>
                    {" "}
                    An error occurred while creating the entity. Error:{" "}
                    {status?.errorMessage ?? "Unknown"}. <br />
                    If you cannot determine how to fix this issue, try
                    refreshing, or contact us to get help.
                </p>
            </Alert>
        );
    } else {
        const id = status.data.created_item?.id ?? "";
        content = (
            <Alert
                severity={"success"}
                action={
                    <Stack direction="column" spacing={2}>
                        <Button
                            onClick={() => {
                                let win = window.open(`/item/${id}`, "_self");
                                win?.focus();
                            }}
                            variant="outlined"
                        >
                            VIEW
                        </Button>
                        <Button
                            onClick={() => {
                                let win = window.open(`/records`, "_self");
                                win?.focus();
                            }}
                            variant="outlined"
                        >
                            EXPLORE REGISTRY
                        </Button>
                    </Stack>
                }
            >
                <AlertTitle>Success</AlertTitle>
                Successfully created the new item. ID: {id}.
            </Alert>
        );
    }

    return <div>{content} </div>;
};

interface UpdateItemResultDisplayComponentProps {
    updateHook: ReturnType<typeof useUpdateItem>;
    id: string;
}
const UpdateItemResultDisplayComponent = (
    props: UpdateItemResultDisplayComponentProps
) => {
    /**
    Component: UpdateItemResultDisplayComponent
    
    Displays the results of updating an item.
    */
    const classes = useStyles();
    const status = props.updateHook.response;
    var content: JSX.Element = <p></p>;
    if (status?.loading) {
        content = (
            <Stack direction="column" justifyContent="center">
                <Stack
                    direction="row"
                    spacing={2}
                    alignItems="center"
                    justifyContent="center"
                >
                    <Typography variant="subtitle1">
                        Submitting...please wait
                    </Typography>
                    <CircularProgress />
                </Stack>
            </Stack>
        );
    } else if (
        status?.error ||
        status === undefined ||
        status?.data === undefined
    ) {
        content = (
            <Alert severity={"error"}>
                <AlertTitle>Error</AlertTitle>
                <p>
                    {" "}
                    An error occurred while updating the entity. Error:{" "}
                    {status?.errorMessage ?? "Unknown"}. <br />
                    If you cannot determine how to fix this issue, try
                    refreshing, or contact us to get help.
                </p>
            </Alert>
        );
    } else {
        content = (
            <Alert
                severity={"success"}
                action={
                    <Stack direction="column" spacing={2}>
                        <Button
                            onClick={() => {
                                let win = window.open(
                                    `/item/${props.id}`,
                                    "_self"
                                );
                                win?.focus();
                            }}
                            variant="outlined"
                        >
                            VIEW
                        </Button>
                        <Button
                            onClick={() => {
                                let win = window.open(`/records`, "_self");
                                win?.focus();
                            }}
                            variant="outlined"
                        >
                            EXPLORE REGISTRY
                        </Button>
                    </Stack>
                }
            >
                <AlertTitle>Success</AlertTitle>
                Successfully updated the item with ID: {props.id}.
            </Alert>
        );
    }

    return <div>{content} </div>;
};

interface SchemaLoadingDisplayComponentProps {
    uiSchema: LoadedEntity<any>;
    jsonSchema: LoadedEntity<any>;
}
const SchemaLoadingDisplayComponent = (
    props: SchemaLoadingDisplayComponentProps
) => {
    /**
    Component: SchemaLoadingDisplayComponent
    
    Displays the status of the schema fetch - including possibly an error. 

    Should be displayed under any condition where the result is an undefined schema.
    */
    const classes = useStyles();

    const combinedState = combineLoadStates([props.uiSchema, props.jsonSchema]);

    const loading = combinedState.loading;
    const error =
        combinedState.error ||
        (!loading &&
            (props.uiSchema?.data === undefined ||
                props.jsonSchema?.data === undefined));
    const errorMessage =
        combinedState.errorMessage ??
        "An error occurred while fetching the UI and JSON schemas for this model.";

    var content: JSX.Element = <p></p>;

    if (loading) {
        content = <CircularProgress />;
    } else if (error) {
        content = <p>An error occurred {errorMessage}.</p>;
    } else {
        content = <p>Schema loaded successfully.</p>;
    }

    return <div className={classes.stackContainer}>{content}</div>;
};

interface AccessStatusDisplayComponentProps {
    accessCheck: ReturnType<typeof useAccessCheck>;
}
const AccessStatusDisplayComponent = (
    props: AccessStatusDisplayComponentProps
) => {
    /**
    Component: AccessStatusDisplayComponent

    Displays the loading/status of the access check - only used in the case that
    access is not yet granted
    */
    const classes = useStyles();
    const status = props.accessCheck;
    var content: JSX.Element = <p></p>;

    if (status.loading) {
        content = (
            <Stack justifyContent="center" direction="row">
                <CircularProgress />;
            </Stack>
        );
    } else if (status.error) {
        content = (
            <Alert severity={"error"}>
                <AlertTitle>Error</AlertTitle>
                <p>
                    {" "}
                    An error occurred while retrieving access information.
                    Error: {status.errorMessage ?? "Unknown"}. <br />
                    If you cannot determine how to fix this issue, try
                    refreshing, or contact us to get help.
                </p>
            </Alert>
        );
    } else if (!status.error && !status.loading && !status.granted) {
        content = <p>Access not granted</p>;
    } else {
        content = <p>Access granted</p>;
    }

    return <div className={classes.stackContainer}>{content}</div>;
};

interface RegisterUpdateFormProps {
    jsonSchema: {};
    uiSchema: {};
    formData: {};
    setFormData: (formData: DomainInfoBase) => void;
    onSubmit: () => void;
    submitEnabled: boolean;
    submitDisabledReason?: string;
}
const RegisterUpdateForm = (props: RegisterUpdateFormProps) => {
    /**
    Component: RegisterUpdateForm
    
    Contains the auto generated form. Provides interface into the state.

    This is a controlled component.
    */

    // css styling
    const classes = useStyles();

    return (
        <div className={classes.stackContainer}>
            <Form
                schema={props.jsonSchema as RJSFSchema}
                uiSchema={props.uiSchema}
                fields={customFields}
                widgets={customWidgets}
                formData={props.formData}
                validator={validator}
                onChange={(d) => {
                    props.setFormData(d.formData);
                }}
                onSubmit={(form) => {
                    props.onSubmit();
                }}
            >
                <Grid container item xs={12}>
                    <Grid
                        container
                        item
                        xs={12}
                        className={classes.interactionContainer}
                    >
                        <Grid
                            container
                            item
                            xs={12}
                            className={classes.interactionPanel}
                            direction="row"
                        >
                            <Button
                                variant="outlined"
                                href="/"
                                className={classes.mainActionButton}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="contained"
                                type="submit"
                                className={classes.mainActionButton}
                                disabled={!props.submitEnabled}
                            >
                                Submit
                            </Button>
                        </Grid>
                        {!props.submitEnabled &&
                            props.submitDisabledReason !== undefined && (
                                <Grid item xs={12}>
                                    <Alert
                                        variant="outlined"
                                        severity="warning"
                                    >
                                        {props.submitDisabledReason}
                                    </Alert>
                                </Grid>
                            )}
                    </Grid>
                </Grid>
            </Form>
        </div>
    );
};

interface AlertErrorComponentProps {
    title: string;
    errorContent: JSX.Element;
}
const AlertErrorComponent = (props: AlertErrorComponentProps) => {
    /**
    Component: AlertErrorComponent

    Generic error display component which renders nicely in register form

    */
    const classes = useStyles();
    return (
        <div className={classes.stackContainer}>
            <Alert
                severity="error"
                variant="outlined"
                className={classes.stackContainer}
            >
                <AlertTitle>{props.title}</AlertTitle>
                {props.errorContent}
            </Alert>
        </div>
    );
};

interface MissingIdComponentProps {}
const MissingIdComponent = (props: MissingIdComponentProps) => {
    /**
    Component: MissingIdComponent

    Displays error alert mentioning that no id was provided for either a clone
    or edit operation.

    */
    const classes = useStyles();
    return (
        <AlertErrorComponent
            title={""}
            errorContent={
                <p>
                    No ID was provided for the clone or edit operation. No
                    action can be taken. Click{" "}
                    <b>
                        <a href="/">here</a>
                    </b>{" "}
                    to return home.
                </p>
            }
        />
    );
};

type RegisterMode = "new" | "clone" | "edit";

interface RegisterEntityProps {
    mode: RegisterMode;
}

const RegisterEntity = observer((props: RegisterEntityProps) => {
    const classes = useStyles();

    // Use keycloak to help with data autofill
    const kc = useKeycloak();

    // Authorisation check
    const auth = useAccessCheck({
        componentName: "entity-registry",
        desiredAccessLevel: "WRITE",
    });

    // Some helpers
    const isCreateMode = props.mode === "new";
    const isCloneMode = props.mode === "clone";
    const isEditMode = props.mode === "edit";

    // Use query string variable hook to retrieve the id
    const { value: id } = useQueryStringVariable({
        queryStringKey: "id",
        readOnly: true,
    });

    // What's the current data in the form? If any
    const [formData, setFormData] = useState<{}>({});

    // Reason for update where applicable
    const [reason, setReason] = useState<string | undefined>(undefined);

    // Subtype - selectable or determined if editing. Provide a default for
    // selection
    const defaultSelectedSubtype = registerableEntityTypes[0];
    const { value: selectedItemSubType, setValue: setSelectedItemSubType } =
        useTypedQueryStringVariable<ItemSubType>({
            queryStringKey: subtypeQStringKey,
            defaultValue: defaultSelectedSubtype,
        });

    // Instead of showing any form - just show a redirect to other component on
    // some subtypes
    const redirectConfiguration: RedirectConfiguration | undefined =
        selectedItemSubType
            ? subtypeRedirects.get(selectedItemSubType)
            : undefined;

    // Show redirect precludes input and form generation
    const showRedirect = redirectConfiguration !== undefined;

    // Manage fetching schema and possibly the existing item
    const formSetup = useFormSetup({
        id: id,
        // Only supply specified subtype if we are in create mode
        subtype: isCreateMode ? selectedItemSubType : undefined,
        // Editing flags requirement to fetch data
        editing: isEditMode || isCloneMode,
        enabled: auth.fallbackGranted && !showRedirect,

        // When data is loaded set the current form data
        onExistingEntityLoaded(item) {
            setFormData(item);
        },
    });

    // This subtype is either dynamically resolved by edit ID or is selected
    const relevantSubtype = formSetup.subtype;

    // Set the default consent granted value to Peron, when setup the clone mode form.
    useEffect(() => {
        if (isCloneMode && relevantSubtype === "PERSON") {
            if (formSetup.existingItem?.data !== undefined) {
                lodashSet(
                    formSetup.existingItem.data,
                    "ethics_approved",
                    false
                );
            }
        }
    }, [formSetup.existingItem?.data]);

    // Have we submitted? Have we succeeded?
    const [submitted, setSubmitted] = useState<boolean>(false);

    // Whenever the relevant subtype changes *in create mode*, reset the form
    // data
    useEffect(() => {
        if (isCreateMode) {
            setFormData({});
            setSubmitted(false);

            // Input autofills where appropriate
            if (!!relevantSubtype) {
                const possibleAutofill = autofills.get(relevantSubtype);
                if (
                    possibleAutofill !== undefined &&
                    !!kc.keycloak.tokenParsed
                ) {
                    possibleAutofill({
                        tokenParsed: kc.keycloak.tokenParsed!,
                        setFormData,
                    });
                }
            }
        }
    }, [relevantSubtype]);

    // Manage form submission with create/edit hooks
    const createManager = useCreateItem({
        subtype: relevantSubtype,
        data: formData as unknown as DomainInfoBase,
        // Only enable if access granted, correct subtype and in create mode
        enabled: auth.granted && !showRedirect && (isCreateMode || isCloneMode),
    });

    const updateManager = useUpdateItem({
        id: id,
        reason,
        subtype: relevantSubtype,
        data: formData as unknown as DomainInfoBase,
        // Only enable if access granted, correct subtype and in edit mode
        enabled: auth.granted && !showRedirect && isEditMode,
    });

    const selector = (
        <div className={classes.stackContainer}>
            <ItemSubtypeSelector
                selectedItemSubType={
                    selectedItemSubType ?? defaultSelectedSubtype
                }
                onChange={(subtype: ItemSubType) => {
                    setSelectedItemSubType!(subtype);
                }}
                listType="REGISTERABLE"
            ></ItemSubtypeSelector>
        </div>
    );

    // nice name display for subtype
    const displaySubtypeName =
        relevantSubtype && mapSubTypeToPrettyName(relevantSubtype);

    // STATES

    // Invalid action combinations
    const idMissing = (isEditMode || isCloneMode) && id === undefined;

    // Form setup error
    const formSetupError = formSetup.error;
    const formSetupErrorMessage = formSetup.errorMessage;

    // Data loading states
    const loadingSchemas =
        !!formSetup.uiSchema?.loading || !!formSetup.jsonSchema?.loading;
    const loadingItem =
        auth.granted && isEditMode && (formSetup.existingItem?.loading ?? true);

    // Submission handler - uses current form state - doesn't need data from
    // form
    const onFormSubmit = () => {
        // Create op in new/clone mode, update op in edit mode
        switch (props.mode) {
            case "new": {
                createManager.submit();
                break;
            }
            case "clone": {
                createManager.submit();
                break;
            }
            case "edit": {
                updateManager.submit();
                break;
            }
        }
        setSubmitted(true);
        window.scrollTo(0, 0);
    };

    // Is the submit enabled?
    var submitEnabled = true;
    var submitDisabledReason: string | undefined = undefined;

    if (isEditMode && (reason === undefined || reason === "")) {
        submitEnabled = false;
        submitDisabledReason =
            "Please provide a reason for this update using the input at the top of the page.";
    }

    // User link enforcement
    // =====================

    // TODO disable/enable when ready
    const userLinkEnforced =
        relevantSubtype !== "PERSON" && (isCreateMode || isCloneMode);

    const overridedMissingLinkMessage = (
        <p>
            You cannot{" "}
            {isCreateMode
                ? "create"
                : isEditMode
                ? "update"
                : isCloneMode
                ? "clone"
                : "create"}{" "}
            an entity without linking your user account to a Person in the
            Registry. If you are trying to register a Person, use the selection
            tool below to select "Person". For more information, visit{" "}
            <a
                href={userLinkEnforcerDocumentationLink}
                target="_blank"
                rel="noreferrer"
            >
                our documentation
            </a>
            . You can link your user account to a Person by visiting your{" "}
            <a
                href={userLinkEnforcerProfileLink}
                target="_blank"
                rel="noreferrer"
            >
                user profile
            </a>
            .
        </p>
    );

    const linkEnforcer = useUserLinkEnforcer({
        // TODO re-enable when ready - change to userLinkEnforced above
        blockEnabled: false,
        // TODO re-enable when ready
        blockOnError: false,
        missingLinkMessage: overridedMissingLinkMessage,
    });

    // Some state management for showing statuses
    const showCreateResult = (isCreateMode || isCloneMode) && submitted;
    const showUpdateResult = isEditMode && submitted;
    const topPanelLHWidth = showCreateResult || showUpdateResult ? 7 : 12;
    const topPanelRHWidth = 12 - topPanelLHWidth;

    // This component is a stack of other child components which display depending on the state of the system
    return (
        <Stack spacing={2} direction="column">
            {
                // User link service enforcer
            }
            {linkEnforcer.blocked && (
                <div className={classes.stackContainer}>
                    {linkEnforcer.render}
                </div>
            )}
            {
                // Access loading/issue
            }
            {!auth.granted && (
                <AccessStatusDisplayComponent accessCheck={auth} />
            )}
            {
                // Form setup error display
            }
            {formSetupError && (
                <AlertErrorComponent
                    title="Registration Setup Error"
                    errorContent={
                        <p>
                            {`An unexpected error occurred while preparing the
                            form. Error: ${formSetupErrorMessage ?? "Unknown"}.
                            If you cannot resolve this error please contact a
                            system administrator.`}
                        </p>
                    }
                />
            )}
            {
                // Missing id
            }
            {idMissing && <MissingIdComponent />}
            {
                // Selector - show if we are in create mode - always show
            }
            {isCreateMode && selector}
            {
                // Redirect display for certain subtypes
            }
            {
                // Header - show if subtype is resolved and not show redirect
                // This box wraps the header + the status response where
                // applicable - note the mui grid bounded widths
            }
            {!linkEnforcer.blocked &&
                !showRedirect &&
                relevantSubtype !== undefined && (
                    <div className={classes.stackContainer}>
                        <Grid container>
                            <Grid item xs={topPanelLHWidth}>
                                <HeaderBoxComponent
                                    isEditMode={isEditMode}
                                    subtype={relevantSubtype}
                                    linked={linkEnforcer.validLink ?? false}
                                />
                            </Grid>
                            {(showCreateResult || showUpdateResult) && (
                                <Grid item xs={topPanelRHWidth}>
                                    {
                                        // Response from upload/download - displayed when there is a
                                        // response defined from the manager -  even if loading
                                    }
                                    {showCreateResult ? (
                                        <CreateItemResultDisplayComponent
                                            createHook={createManager}
                                        />
                                    ) : (
                                        showUpdateResult && (
                                            <UpdateItemResultDisplayComponent
                                                updateHook={updateManager}
                                                // Id is definitely defined at this point - but provide fall through
                                                id={id ?? "unspecified"}
                                            />
                                        )
                                    )}
                                </Grid>
                            )}
                        </Grid>
                    </div>
                )}
            {!linkEnforcer.blocked && showRedirect && (
                <DisplayRedirect config={redirectConfiguration} />
            )}
            {
                // Loading template - displayed if the template data is not present but the response is in progress
            }
            {!linkEnforcer.blocked &&
                !showRedirect &&
                ((formSetup.uiSchema !== undefined &&
                    formSetup.uiSchema.data === undefined) ||
                    (formSetup.jsonSchema !== undefined &&
                        formSetup.jsonSchema.data === undefined)) && (
                    <SchemaLoadingDisplayComponent
                        uiSchema={formSetup.uiSchema!}
                        jsonSchema={formSetup.jsonSchema!}
                    />
                )}
            {
                // Reason request (when in edit mode)
            }
            {!linkEnforcer.blocked && isEditMode && (
                <ReasonInputComponent
                    reason={reason ?? ""}
                    setReason={setReason}
                />
            )}
            {
                // Form - contains the moving data and submit/cancel buttons
            }
            {!linkEnforcer.blocked &&
                formSetup.uiSchema?.data &&
                formSetup.jsonSchema?.data && (
                    <RegisterUpdateForm
                        onSubmit={onFormSubmit}
                        submitEnabled={submitEnabled}
                        submitDisabledReason={submitDisabledReason}
                        uiSchema={formSetup.uiSchema.data}
                        jsonSchema={formSetup.jsonSchema.data}
                        formData={formData}
                        setFormData={setFormData}
                    />
                )}
        </Stack>
    );
});

export default RegisterEntity;
