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
import { OptionallyRequiredCheck } from "../shared-interfaces/AuthAPI";

const useStyles = makeStyles((theme: Theme) => createStyles({}));

interface StatusDisplayOptions {
    // Statuses when relevant
    relevantSuccessTitle: string;
    relevantErrorTitle: string;
    relevantErrorContent: JSX.Element;
    relevantSuccessContent: JSX.Element;

    // Statuses when non relevant
    nonRelevantSuccessTitle: string;
    nonRelevantErrorTitle: string;
    nonRelevantErrorContent: JSX.Element;
    nonRelevantSuccessContent: JSX.Element;

    //Description content override
    descriptionContentOverride?: JSX.Element;

}

interface CheckStatusComponentProps extends StatusDisplayOptions {
    relevant: boolean;
    obtained: boolean;
}
const CheckStatusComponent = (props: CheckStatusComponentProps) => {
    /**
    Component: ConsentStatusComponent
    Displays a mui alert depending on the granted/not granted status.
    */

    const success =
        // Main error case - i.e. relevant and not obtained
        !(props.relevant && !props.obtained) &&
        // Edge error case - i.e. non relevant but obtained
        !(!props.relevant && props.obtained);

    const title = props.relevant
        ? success
            ? props.relevantSuccessTitle
            : props.relevantErrorTitle
        : success
        ? props.nonRelevantSuccessTitle
        : props.nonRelevantErrorTitle;

    const bodyContent = props.relevant
        ? success
            ? props.relevantSuccessContent
            : props.relevantErrorContent
        : success
        ? props.nonRelevantSuccessContent
        : props.nonRelevantErrorContent;

    return (
        <Alert variant="outlined" severity={success ? "success" : "warning"}>
            <AlertTitle>{title}</AlertTitle>
            {bodyContent}
        </Alert>
    );
};

// Current selection/value
type DataType = OptionallyRequiredCheck;

export interface OptionallyRequiredConsentOverrideProps
    extends FieldProps<DataType>,
        StatusDisplayOptions {
    // Labels for check boxes
    relevantLabel: string;
    obtainedLabel: string;
}

export const OptionallyRequiredConsentOverride = (
    props: OptionallyRequiredConsentOverrideProps
) => {
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
    const lhWidthRaw = 7;
    const gap = 0.5;
    const lhWidth = lhWidthRaw - gap / 2.0;
    const rhWidth = 12 - lhWidthRaw - gap / 2.0;

    const isRelevant = props.formData?.relevant;
    const isObtained = props.formData?.obtained;

    // Always show relevant checkbox
    const showRelevantCheckbox = true;

    // Do we show obtained checkbox? (Yes if either obtained/relevant)
    const showObtainedCheckbox = (isObtained ?? false) || (isRelevant ?? false);

    const relevantHandler = (e: React.ChangeEvent<HTMLInputElement>) => {
        // Parse tick status
        const ticked = e.target.checked as boolean;

        if (ticked) {
            // If marking as relevant - set relevant true but don't touch
            // obtained
            props.onChange({
                relevant: true,
                obtained: props.formData?.obtained,
            } as DataType);
        } else {
            // If marking as not relevant - clear obtained as well
            props.onChange({
                relevant: false,
                obtained: false,
            } as DataType);
        }
    };
    const obtainedHandler = (e: React.ChangeEvent<HTMLInputElement>) => {
        // Parse tick status
        const ticked = e.target.checked as boolean;
        // Just update obtained
        props.onChange({
            relevant: props.formData?.relevant,
            obtained: ticked,
        } as DataType);
    };

    //check any description content override
    const descriptionContentOverrideBody = props.descriptionContentOverride;

    const uiTitle = props.uiSchema ? props.uiSchema["ui:title"] : undefined;
    const uiDescription = props.uiSchema
        ? props.uiSchema["ui:description"]
        : undefined;

    const title = uiTitle ?? props.schema.title ?? "Required Check";
    const description =
        descriptionContentOverrideBody ??
        uiDescription ??
        props.schema.description ??
        "Please mark whether this check is relevant and obtained.";

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
                    {showRelevantCheckbox && (
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={isRelevant ?? false}
                                    onChange={relevantHandler}
                                ></Checkbox>
                            }
                            label={<b>{props.relevantLabel}</b>}
                        ></FormControlLabel>
                    )}
                    {showObtainedCheckbox && (
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={isObtained ?? false}
                                    onChange={obtainedHandler}
                                ></Checkbox>
                            }
                            label={<b>{props.obtainedLabel}</b>}
                        ></FormControlLabel>
                    )}
                </Stack>
            </Grid>
            {
                // Status
            }
            <Grid item xs={rhWidth}>
                <CheckStatusComponent
                    relevant={isRelevant ?? false}
                    obtained={isObtained ?? false}
                    {...props}
                />
            </Grid>
        </Grid>
    );
};

