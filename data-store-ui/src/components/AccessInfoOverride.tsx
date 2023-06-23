import {
    TextField,
    Checkbox,
    Grid,
    Stack,
    Typography,
    FormGroup,
    FormControlLabel,
    Alert,
    AlertTitle,
} from "@mui/material";
import React, { useEffect } from "react";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";

const useStyles = makeStyles((theme: Theme) =>
    createStyles({
        helperText: {
            marginLeft: 0,
        },
        clearButton: {
            "margin-bottom": theme.spacing(2),
            "margin-top": theme.spacing(2),
        },
    })
);

const DEFAULT_REPOSITED = true;

type FormData = { [k: string]: any };

type SchemaData = {
    title?: string;
    description?: string;
};

interface OverrideProps {
    // This is the form data passed from rjsf
    formData: FormData;

    // This is the change handler from rjsf
    onChange: (data: FormData) => void;

    // title and description for field.
    schema: SchemaData & {
        properties: {
            reposited: SchemaData;
            uri: SchemaData;
            description: SchemaData;
        };
    };

    // ui schema in case overrided
    //uiSchema: {
    //    "ui:description"?: string;
    //};

    // Is this required?
    required: boolean;
}

interface ParsedFormData {
    reposited?: boolean;
    uri?: string;
    description?: string;
}

const parseFormData = (formData: FormData): ParsedFormData => {
    // There is a bug in the custom form which doesn't pass in the value of
    // reposited if its false - so assume if uri/description are present but
    // reposited value isn't, that it is false
    console.log("INPUT: ", formData);
    const uriOrDesc =
        formData["uri"] !== undefined || formData["description"] !== undefined;

    // Never set reposited to undefined
    const output = {
        reposited:
            formData["reposited"] ?? (uriOrDesc ? false : DEFAULT_REPOSITED),
        uri: formData["uri"] ?? undefined,
        description: formData["description"] ?? undefined,
    };
    console.log("OUTPUT:", output);
    return output;
};

const AccessInfoOverride = (props: OverrideProps) => {
    /**
     */

    console.log("Rendering custom");
    console.log(JSON.stringify(props.formData));

    // Parse defaults/input
    const parsedFormData = parseFormData(props.formData);

    const updateFormData = (parsedFormData: ParsedFormData) => {
        console.log("Updating form data");
        const newFormData: ParsedFormData = JSON.parse(
            JSON.stringify(parsedFormData)
        );
        if (newFormData.reposited) {
            delete newFormData["description"];
            delete newFormData["uri"];
        }
        console.log("Updating with", JSON.stringify(newFormData));
        props.onChange(newFormData);
    };

    // Force an initial update - this is required because of the bug with not
    // showing the false value in the form data despite it being present in the
    // payload JSON
    useEffect(() => {
        updateFormData(parsedFormData);
    }, []);

    const repositedDisplay = parsedFormData.reposited ?? true;

    return (
        <Stack spacing={2.5}>
            <Grid
                container
                justifyContent="flex-start"
                spacing={3}
                alignItems="center"
            >
                {
                    // Title and description
                }
                <Grid item xs={5}>
                    <Typography variant="h6">{props.schema.title}</Typography>
                    <Typography variant="subtitle1">
                        {props.schema.description}
                    </Typography>
                </Grid>

                {
                    // Enabled checkbox
                }
                <Grid item>
                    <FormGroup>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={
                                        parsedFormData.reposited ??
                                        DEFAULT_REPOSITED
                                    }
                                    onChange={(e) => {
                                        const current =
                                            parsedFormData.reposited ??
                                            DEFAULT_REPOSITED;
                                        var newData: ParsedFormData =
                                            JSON.parse(
                                                JSON.stringify(parsedFormData)
                                            );
                                        newData.reposited = !current;
                                        updateFormData(newData);
                                    }}
                                />
                            }
                            label={"Store data in the Data Store"}
                        />
                    </FormGroup>
                </Grid>
            </Grid>
            <Alert
                variant="standard"
                color={repositedDisplay ? "success" : "warning"}
            >
                <AlertTitle>
                    {repositedDisplay
                        ? "Stored in the data store"
                        : "Stored elsewhere"}
                </AlertTitle>
                {repositedDisplay
                    ? "Your dataset will be stored in the Data Store."
                    : "Your dataset is available from the below source. It will not be stored in the Data Store."}
            </Alert>
            {!repositedDisplay && (
                <React.Fragment>
                    <div>
                        <Typography variant="subtitle1">
                            {props.schema.properties.uri.title}
                        </Typography>
                        <Typography variant="subtitle2">
                            {props.schema.properties.uri.description}
                        </Typography>
                        <TextField
                            required
                            fullWidth
                            value={parsedFormData.uri ?? ""}
                            onChange={(e) => {
                                var newData: ParsedFormData = JSON.parse(
                                    JSON.stringify(parsedFormData)
                                );
                                newData.uri = e.target.value;
                                updateFormData(newData);
                            }}
                            disabled={parsedFormData.reposited}
                        />
                    </div>
                    <div>
                        <Typography variant="subtitle1">
                            {props.schema.properties.description.title}
                        </Typography>
                        <Typography variant="subtitle2">
                            {props.schema.properties.description.description}
                        </Typography>
                        <TextField
                            value={parsedFormData.description ?? ""}
                            required
                            multiline
                            fullWidth
                            minRows={4}
                            onChange={(e) => {
                                var newData: ParsedFormData = JSON.parse(
                                    JSON.stringify(parsedFormData)
                                );
                                newData.description = e.target.value;
                                updateFormData(newData);
                            }}
                            disabled={parsedFormData.reposited}
                        />
                    </div>
                </React.Fragment>
            )}
        </Stack>
    );
};

export default AccessInfoOverride;
