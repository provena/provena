import {
    Checkbox,
    FormControlLabel,
    Grid,
    Stack,
    TextField,
    Typography,
} from "@mui/material";
import { FieldProps } from "@rjsf/utils";
import { useEffect, useState } from "react";
import { deriveTitleDescription } from "../util";

export type OptionalStringDataType = string | undefined;

export interface OptionalStringFieldOverrideComponentProps
    extends FieldProps<OptionalStringDataType> {
    // Message for tickbox
    tickboxMessage: string;
    // Message for text input placeholder
    inputPlaceholderText: string;
}

export const OptionalStringFieldOverrideComponent = (
    props: OptionalStringFieldOverrideComponentProps
) => {
    /**
    Component: OptionalStringFieldOverrideComponent
    
    */

    // determine if we are including the value
    const [included, setIncluded] = useState<boolean>(
        props.formData !== undefined
    );

    const { title, description } =
        deriveTitleDescription<OptionalStringDataType>(props);

    // If the box is unticked - clear any input
    useEffect(() => {
        if (!included) {
            props.onChange(undefined);
        }
    }, [included]);

    return (
        <Stack direction="column" spacing={1}>
            {
                // Heading
            }
            <Typography variant="h6">{title}</Typography>
            {
                // Description
            }
            <Typography variant="subtitle1">{description}</Typography>

            <Grid
                container
                alignItems="center"
                justifyContent="space-between"
                padding={1}
            >
                <Grid item>
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={included}
                                onChange={(e) => {
                                    setIncluded(e.target.checked);
                                }}
                            ></Checkbox>
                        }
                        label={<b>{props.tickboxMessage}</b>}
                    ></FormControlLabel>
                </Grid>
                <Grid item xs={7}>
                    <TextField
                        // This should be required because it is only rendered
                        // when the user specifies including a citation
                        required={included}
                        disabled={!included}
                        fullWidth
                        value={props.formData ?? ""}
                        onChange={(e) => {
                            const val = e.target.value;
                            // Never send empty string
                            if (val === "") {
                                props.onChange(undefined);
                            }
                            // Otherwise update with value
                            else {
                                props.onChange(val);
                            }
                        }}
                        label={props.inputPlaceholderText}
                    />
                </Grid>
            </Grid>
        </Stack>
    );
};
