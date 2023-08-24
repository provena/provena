import {
    Alert,
    Button,
    Container,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Grid,
    Stack,
    TextField,
    Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import Form from "@rjsf/mui";
import { UiSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { observer } from "mobx-react-lite";
import React, { useEffect, useRef, useState } from "react";
import {
    useUserLinkEnforcer,
    userLinkEnforcerDocumentationLink,
    userLinkEnforcerProfileLink,
} from "react-libs";
import { useHistory, useParams } from "react-router-dom";
import updateStore from "../stores/registerOrModifyStore";
import { fields, uiSchema } from "../util/formUtil";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        root: {
            display: "flex",
            flexWrap: "wrap",
            flexFlow: "column",
            justifyContent: "center",
            alignItems: "center",
            backgroundColor: "white",
            padding: theme.spacing(4),
            marginBottom: 20,
            minHeight: "60vh",
            borderRadius: 5,
        },
        button: {
            marginRight: theme.spacing(1),
        },
        instructions: {
            marginTop: theme.spacing(1),
            marginBottom: theme.spacing(1),
        },
        centerLoading: {
            display: "flex",
            justifyContent: "center",
        },
    })
);
const overrideMissingLinkMessage = (
    <p>
        You cannot modify a Dataset without linking your user account to a
        registered Person in the Registry. For more information, visit{" "}
        <a
            href={userLinkEnforcerDocumentationLink}
            target="_blank"
            rel="noreferrer"
        >
            our documentation
        </a>
        . You can link your user account to a Person by visiting your{" "}
        <a href={userLinkEnforcerProfileLink} target="_blank" rel="noreferrer">
            user profile
        </a>
        .
    </p>
);

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
        <Stack direction="column" spacing={2}>
            <Typography variant="subtitle1">
                Please provide an explanation for why this update is required*
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
    );
};

interface UpdateMetadataParams {
    id: string;
}

type UpdateMode = "clone" | "edit";

interface UpdateMetadataProps {
    mode: UpdateMode;
}

//for lodash set update values based on the labelPath
export interface LabelPathAndValue {
    labelPath: string;
    value: unknown;
}

// Set approvals obtained labels to "false" when initiate the form in clone mode
const labelValueInitialSet: LabelPathAndValue[] = [
    { labelPath: "approvals.ethics_registration.obtained", value: false },
    { labelPath: "approvals.ethics_access.obtained", value: false },
    { labelPath: "approvals.indigenous_knowledge.obtained", value: false },
    { labelPath: "approvals.export_controls.obtained", value: false },
];

// Set initial reposited, to avoid reposited be undefined
const initializeRepositedValue = () => {
    const access_info_path = "dataset_info.access_info";

    const repositedValue = updateStore.getLabelValue(
        access_info_path + ".reposited"
    );
    const uriValue = updateStore.getLabelValue(access_info_path + ".uri");
    const descriptionValue = updateStore.getLabelValue(
        access_info_path + ".description"
    );

    // If uri/description are present but reposited value isn't, then reposited value should be false
    const uriOrDesc =
        (uriValue.status && uriValue.value !== undefined) ||
        (descriptionValue.status && descriptionValue.value !== undefined);

    if (
        repositedValue.status &&
        (repositedValue.value === undefined || repositedValue.value === null)
    ) {
        // Default reposited value is true
        const repositedRes = uriOrDesc ? false : true;
        updateStore.setLabelValue([
            { labelPath: access_info_path + ".reposited", value: repositedRes },
        ]);
    }
};

const UpdateMetadata = observer((props: UpdateMetadataProps) => {
    const { id: handle_id } = useParams<UpdateMetadataParams>();
    const history = useHistory();
    const classes = useStyles();
    useEffect(() => {
        updateStore.loadSchemaExisting(handle_id);
    }, []);

    // Do we need a reason?
    const reasonRequired = props.mode === "edit";

    // In clone mode? for consent granted default set
    const isCloneMode = props.mode === "clone";

    // For setting initial values at initial render, pay attention on the wrapping observer.
    const needToSetInitialValue = useRef(true);

    useEffect(() => {
        if (
            needToSetInitialValue.current &&
            updateStore.currentValue !== undefined
        ) {
            // For initiating values
            if (isCloneMode) {
                // For clone mode initialize values only
                // Set label values when initialize the form in clone mode
                updateStore.setLabelValue(labelValueInitialSet);
            }
            // For both clone mode and edit mode
            // Initialize reposited value, and never set it to undefined
            initializeRepositedValue();

            // Initialized
            needToSetInitialValue.current = false;
        }
    }, [updateStore.currentValue]);

    // Reason for update where applicable
    const [reason, setReason] = useState<string | undefined>(undefined);

    // Is the submit enabled?
    var submitEnabled = true;
    var submitDisabledReason: string | undefined = undefined;

    if (reasonRequired && (reason === undefined || reason === "")) {
        submitEnabled = false;
        submitDisabledReason =
            "Please provide a reason for this update using the input at the top of the page.";
    }

    // user id link enforcer (enabled for Datasets)
    const linkEnforcer = useUserLinkEnforcer({
        blockEnabled: true,
        blockOnError: true,
        missingLinkMessage: overrideMissingLinkMessage,
    });

    // display error if link is not established
    if (linkEnforcer.blocked) {
        return (
            <div className={classes.root} style={{ width: "100%" }}>
                {linkEnforcer.render}
            </div>
        );
    }

    const dialogFragment = (
        <React.Fragment>
            {
                //Processing dialogue based on store state
            }
            <Dialog open={updateStore.processing}>
                <DialogTitle>{updateStore.processing}</DialogTitle>
                <DialogContent>
                    <DialogContent>
                        <p>{updateStore.processingMessage}</p>
                    </DialogContent>
                </DialogContent>
            </Dialog>

            {
                //Error dialogue based on store state
            }
            <Dialog open={updateStore.error}>
                <DialogTitle> Error </DialogTitle>
                <DialogContent>
                    <DialogContent>
                        <p>
                            {updateStore.errorMessage ??
                                "No error message provided."}
                        </p>
                    </DialogContent>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => updateStore.closeErrorDialog()}>
                        Dismiss
                    </Button>
                </DialogActions>
            </Dialog>
        </React.Fragment>
    );

    if (updateStore.schemaReady) {
        // Display the schema
        return (
            <div className={classes.root}>
                <Stack direction="column" spacing={2}>
                    <Typography variant="h4">
                        {props.mode === "edit" ? "Updating" : "Cloning"} Dataset
                        ({handle_id})
                    </Typography>
                    {reasonRequired && (
                        <ReasonInputComponent
                            reason={reason ?? ""}
                            setReason={setReason}
                        />
                    )}
                    <Form
                        schema={updateStore.schema}
                        uiSchema={uiSchema as UiSchema}
                        validator={validator}
                        fields={fields}
                        onError={(errors) => {
                            console.log("Errors");
                            console.log(
                                JSON.stringify(updateStore.currentValue)
                            );
                        }}
                        onSubmit={({ formData }) => {
                            console.log(formData);
                            switch (props.mode) {
                                case "edit": {
                                    reason !== undefined &&
                                        updateStore.updateMetadataAction(
                                            formData,
                                            history,
                                            reason
                                        );
                                    break;
                                }
                                case "clone": {
                                    updateStore.registerDatasetAction(
                                        formData,
                                        history
                                    );
                                    break;
                                }
                            }
                        }}
                        onChange={({ formData }) => {
                            updateStore.onFormChange(formData);
                        }}
                        formData={updateStore.currentValue}
                        id="registration-form"
                    >
                        <Stack direction="column" spacing={2}>
                            <Stack
                                direction="row"
                                justifyContent="space-between"
                            >
                                <Button variant="outlined" href="/">
                                    Cancel
                                </Button>
                                <Button
                                    variant="contained"
                                    type="submit"
                                    disabled={!submitEnabled}
                                >
                                    Submit
                                </Button>
                            </Stack>
                            {!submitEnabled &&
                                submitDisabledReason !== undefined && (
                                    <Grid item xs={12}>
                                        <Alert
                                            variant="outlined"
                                            severity="warning"
                                        >
                                            {submitDisabledReason}
                                        </Alert>
                                    </Grid>
                                )}
                        </Stack>
                    </Form>
                </Stack>
                {dialogFragment}
            </div>
        );
    } else if (updateStore.loading) {
        // Otherwise get the schema
        return (
            <div className={classes.root}>
                Please wait... retrieving schema form.
                {dialogFragment}
            </div>
        );
    } else {
        // Otherwise get the schema
        return (
            <div className={classes.root}>
                Schema form retrieval failure - try refreshing once you have
                resolved the errors.
                {dialogFragment}
            </div>
        );
    }
});

export default UpdateMetadata;
