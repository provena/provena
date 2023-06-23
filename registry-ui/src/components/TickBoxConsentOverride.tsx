import {
    Alert,
    AlertTitle,
    Checkbox,
    FormControlLabel,
    Stack,
    Typography,
    Grid,
} from "@mui/material";
import React from "react";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";
import { FieldProps } from "@rjsf/utils";

const useStyles = makeStyles((theme: Theme) => createStyles({}));

interface ConsentStatusComponentProps {
    granted: boolean;
    successTitleOverride?: string;
    errorTitleOverride?: string;
    errorContentOverride?: JSX.Element;
    successContentOverride?: JSX.Element;
}
const ConsentStatusComponent = (props: ConsentStatusComponentProps) => {
    /**
    Component: ConsentStatusComponent
    Displays a mui alert depending on the granted/not granted status.
    */
    const defaultErrorTitle = "Consent must be granted to proceed.";
    const defaultSuccessTitle = "Consent granted";
    const defaultErrorContent = (
        <p>You need to provide consent to be able to register this item.</p>
    );
    const defaultSuccessContent = (
        <p>Consent is granted and the item can be registered.</p>
    );

    return (
        <Alert
            variant="outlined"
            severity={props.granted ? "success" : "warning"}
        >
            <AlertTitle>
                {props.granted
                    ? props.successTitleOverride ?? defaultSuccessTitle
                    : props.errorTitleOverride ?? defaultErrorTitle}
            </AlertTitle>
            {props.granted
                ? props.successContentOverride ?? defaultSuccessContent
                : props.errorContentOverride ?? defaultErrorContent}
        </Alert>
    );
};

// Current selection/value
type TickBoxType = boolean | undefined;

export interface TickBoxOverrideProps extends FieldProps<TickBoxType> {
    // Ethics description field
    additionalDescription?: string | JSX.Element;

    // Overrides
    successTitleOverride?: string;
    errorTitleOverride?: string;
    errorContentOverride?: JSX.Element;
    successContentOverride?: JSX.Element;
}

export const TickBoxOverride = (props: TickBoxOverrideProps) => {
    /**
     *  Component TickBoxOverride

    This is a rjsf field override (once some additional fields are populated)..

    Note that the title and description go in this order

    1) additional provided
    2) ui schema
    3) json schema 
    4) fallback default

     */

    const classes = useStyles();

    // Layout config
    const lhWidthRaw = 6;
    const gap = 0.5;
    const lhWidth = lhWidthRaw - gap / 2.0;
    const rhWidth = 12 - lhWidthRaw - gap / 2.0;

    // Derive ticked state from the form data
    const isTicked = props.formData === undefined ? false : props.formData;

    const checkBoxHandler = (e: React.ChangeEvent<HTMLInputElement>) => {
        const ticked = e.target.checked as boolean;
        props.onChange(ticked);
    };

    const uiTitle = props.uiSchema ? props.uiSchema["ui:title"] : undefined;
    const uiDescription = props.uiSchema
        ? props.uiSchema["ui:description"]
        : undefined;

    const title = uiTitle ?? props.schema.title ?? "Consent";
    const description =
        props.additionalDescription ??
        uiDescription ??
        props.schema.description ??
        "Please provide consent to register this item";

    return (
        <Grid container justifyContent="space-between" alignItems="center">
            <Grid item xs={lhWidth}>
                <Stack direction="column" spacing={1}>
                    {
                        // Heading
                    }
                    <Typography variant="h6">{title}</Typography>
                    {
                        // Description
                    }
                    <Typography variant="subtitle1">{description}</Typography>
                    {
                        // Control
                    }
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={isTicked}
                                onChange={checkBoxHandler}
                            ></Checkbox>
                        }
                        label={<b>Consent Granted?</b>}
                    ></FormControlLabel>
                </Stack>
            </Grid>
            {
                // Status
            }
            <Grid item xs={rhWidth}>
                <ConsentStatusComponent granted={isTicked} {...props} />
            </Grid>
        </Grid>
    );
};
