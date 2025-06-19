import {
  Alert,
  AlertTitle,
  Checkbox,
  FormControlLabel,
  Stack,
  Typography,
  Grid,
  InputLabel,
  FormControl,
  Button,
  TextField,
} from "@mui/material";
import React from "react";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { Theme } from "@mui/material/styles";
import { FieldProps } from "@rjsf/utils";
import { OptionallyRequiredDate } from "provena-interfaces/RegistryAPI";
import { DesktopDatePicker } from "@mui/x-date-pickers";
import { AdapterMoment } from "@mui/x-date-pickers/AdapterMoment";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import moment from "moment";

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
  dateProvided: boolean;
}

const CheckStatusComponent = (props: CheckStatusComponentProps) => {
  const getAlertInfo = () => {
    if (!props.relevant) {
      return {
        severity: "warning",
        title: props.nonRelevantErrorTitle,
        content: props.nonRelevantErrorContent,
      };
    } else if (!props.dateProvided) {
      return {
        severity: "error",
        title: props.relevantErrorTitle,
        content: props.relevantErrorContent,
      };
    } else {
      return {
        severity: "success",
        title: props.relevantSuccessTitle,
        content: props.relevantSuccessContent,
      };
    }
  };

  const { severity, title, content } = getAlertInfo();

  return (
    <Alert
      variant="outlined"
      severity={severity as "warning" | "error" | "success"}
    >
      <AlertTitle>{title}</AlertTitle>
      {content}
    </Alert>
  );
};

// Current selection/value
type DataType = OptionallyRequiredDate;

export interface OptionallyRequiredDateOverrideProps
  extends FieldProps<DataType>,
    StatusDisplayOptions {
  // Labels for check box and date input
  relevantLabel: string;
  dateLabel: string;
}

export const OptionallyRequiredDateOverride = (
  props: OptionallyRequiredDateOverrideProps
) => {
  /**
     *  Component OptionallyRequiredDateOverride

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
  // This is a date
  const date = props.formData?.value;

  // Always show relevant checkbox
  const showRelevantCheckbox = true;

  // Do we show obtained checkbox? (Yes if either obtained/relevant)
  const showDateInput = !!date || isRelevant;
  console.log("show date: " + showDateInput);

  const relevantHandler = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Parse tick status
    const ticked = e.target.checked as boolean;

    if (ticked) {
      // If marking as relevant - set relevant true but don't touch
      // obtained
      props.onChange({
        relevant: true,
        value: props.formData?.value,
      } as DataType);
    } else {
      // If marking as not relevant - clear obtained as well
      props.onChange({
        relevant: false,
      } as DataType);
    }
  };

  const dateSetHandler = (dateString: string | undefined) => {
    // Just update obtained
    props.onChange({
      relevant: props.formData?.relevant,
      value: dateString,
    } as DataType);
  };

  //check any description content override
  const descriptionContentOverrideBody = props.descriptionContentOverride;

  const uiTitle = props.uiSchema ? props.uiSchema["ui:title"] : undefined;
  const uiDescription = props.uiSchema
    ? props.uiSchema["ui:description"]
    : undefined;

  const title = uiTitle ?? props.schema.title ?? "Required Date";
  const description =
    descriptionContentOverrideBody ??
    uiDescription ??
    props.schema.description ??
    "Please mark whether this date is relevant.";

  const setTodayDate = () => {
    const today = moment().format("YYYY-MM-DD");
    dateSetHandler(today);
  };

  return (
    <LocalizationProvider dateAdapter={AdapterMoment}>
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

            {showDateInput && (
              <Grid container spacing={2} alignItems="flex-start">
                <Grid item>
                  <FormControl>
                    <DesktopDatePicker
                      value={
                        props.formData?.value
                          ? moment(props.formData.value)
                          : null
                      }
                      onChange={(date) => {
                        dateSetHandler(
                          date ? date.format("YYYY-MM-DD") : undefined
                        );
                      }}
                      renderInput={(params) => (
                        <TextField {...params} fullWidth />
                      )}
                    />
                    <InputLabel
                      sx={{
                        position: "relative",
                        transform: "none",
                        marginTop: 1,
                      }}
                    >
                      {props.dateLabel}
                    </InputLabel>
                  </FormControl>
                </Grid>
                <Grid item>
                  <Button variant="outlined" onClick={setTodayDate}>
                    Set to today
                  </Button>
                </Grid>
              </Grid>
            )}
          </Stack>
        </Grid>
        {
          // Status
        }
        <Grid item xs={rhWidth}>
          <CheckStatusComponent
            relevant={isRelevant ?? false}
            dateProvided={!!props.formData?.value}
            {...props}
          />
        </Grid>
      </Grid>
    </LocalizationProvider>
  );
};
