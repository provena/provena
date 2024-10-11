import {
  Alert,
  Button,
  Grid,
  List,
  ListItem,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { ErrorListProps, RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import {
  AutoCompleteDatasetLookup,
  AutoCompleteDatasetTemplateLookup,
  AutoCompleteModelRunWorkflowDefinitionLookup,
  AutoCompleteOrganisationLookup,
  AutoCompletePersonLookup,
  AutoCompleteStudyLookup,
  DatasetTemplateAdditionalAnnotationsOverride,
  DatasetTemplateDisplay,
  Form,
  UnixTimestampField,
} from "react-libs";
import ArrayField from "react-libs/components/FixedArrayOverride/FixedArrayField";
import ErrorIcon from "@material-ui/icons/Error";
import ErrorOutlineIcon from "@material-ui/icons/ErrorOutline";

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    interactionContainer: {
      padding: theme.spacing(1),
    },
    interactionPanel: {
      display: "flex",
      justifyContent: "space-around",
      alignItems: "center",
      backgroundColor: "white",
      padding: theme.spacing(1),
      borderRadius: 5,
    },
    mainActionButton: {
      marginBottom: theme.spacing(2),
      width: "40%",
    },
    stackContainer: {
      backgroundColor: "white",
      borderRadius: 5,
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
      paddingTop: theme.spacing(1),
      paddingBottom: theme.spacing(1),
    },
    errorListContainer: {
      backgroundColor: "#FFF5F5", // Light pink background
      borderRadius: theme.shape.borderRadius,
      padding: theme.spacing(2),
      marginBottom: theme.spacing(2),
      border: "1px solid #FFA5A5", // Light red border
    },
    errorListTitle: {
      color: "#D32F2F", // Dark red color for title
      marginBottom: theme.spacing(2),
      display: "flex",
      alignItems: "center",
      fontWeight: 600,
    },
    errorListSubtitle: {
      color: theme.palette.common.black, // Dark red color for title
      marginBottom: theme.spacing(2),
      display: "flex",
      alignItems: "center",
      fontWeight: 500,
    },
    errorIcon: {
      marginRight: theme.spacing(1),
      fontSize: "30px",
      color: "#D32F2F", // Dark red color for icon
    },
    errorListList: {
      padding: 0,
    },
    errorListItem: {
      backgroundColor: "#FFFFFF", // White background for each item
      borderRadius: theme.shape.borderRadius,
      marginBottom: theme.spacing(1),
      padding: theme.spacing(1.5, 2),
      boxShadow: "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
      border: "1px solid #FFCCCB", // Very light red border
      "&:last-child": {
        marginBottom: 0,
      },
    },
    errorText: {
      fontFamily: "monospace",
      wordBreak: "break-word",
      color: "#424242", // Dark grey for error text
    },
  })
);

/**
 * Stylizes an error property string by transforming dot notation and array indices
 * into a more readable format.
 *
 * @param property - The error property string to stylize.
 * @returns A stylized version of the property string, or the original string if stylization fails.
 *
 * @example
 * // Returns "inputs[0] -> resources -> deferred"
 * stylizeErrorProperty(".inputs.0.resources.deferred")
 *
 * @example
 * // Returns "data -> items[2] -> name"
 * stylizeErrorProperty("data.items.2.name")
 *
 * @example
 * // Returns the original string if stylization fails
 * stylizeErrorProperty("invalid..property")
 */
function stylizeErrorProperty(property: string): string {
  try {
    // Remove leading dot if present
    const trimmedProperty = property.replace(/^\./, "");

    // Split the property string into parts
    const parts = trimmedProperty.split(".");

    // Transform each part
    const transformedParts = parts.map((part, index) => {
      // Check if the part is a number (array index)
      if (/^\d+$/.test(part)) {
        // If the previous part exists and isn't already an array notation
        if (index > 0 && !parts[index - 1].endsWith("]")) {
          return `[${part}]`;
        }
      }
      return part;
    });

    // Join the parts with " -> " and replace ".[]" with "[]"
    return transformedParts.join(" -> ").replace(/\.\[/g, "[");
  } catch (error) {
    // If any error occurs during the process, return the original string
    return property;
  }
}

// TODO get from prov-api
export const MODEL_RUN_JSON_SCHEMA = {
  type: "object",
  definitions: {
    datasetItem: {
      type: "object",
      properties: {
        dataset_template_id: { type: "string" },
        dataset_id: { type: "string" },
        resources: {
          type: "object",
          additionalProperties: { type: "string", minLength: 1 },
        },
      },
      required: ["dataset_id"],
    },
  },
  properties: {
    display_name: { type: "string" },
    description: { type: "string" },
    model_version: { type: "string" },
    start_time: { type: "number" },
    end_time: { type: "number" },
    study_id: { type: "string" },
    associations: {
      type: "object",
      properties: {
        modeller_id: { type: "string" },
        requesting_organisation_id: { type: "string" },
      },
      required: ["modeller_id"],
    },
    inputs: {
      type: "array",
      items: { $ref: "#/definitions/datasetItem" },
    },
    outputs: {
      type: "array",
      items: { $ref: "#/definitions/datasetItem" },
    },
    annotations: {
      type: "object",
      additionalProperties: { type: "string", minLength: 1 },
    },
  },
  required: [
    "inputs",
    "outputs",
    "display_name",
    "description",
    "associations",
    "start_time",
    "end_time",
  ],
};

const DS_SPEC = {
  "ui:title": "Dataset",
  dataset_id: {
    "ui:title": "Dataset",
    "ui:description":
      "Please use the search tool below to select a dataset which satisfies this template.",
    "ui:field": "autoCompleteDatasetLookup",
  },
  resources: {
    "ui:title": "Resources",
    "ui:description":
      "If your template requires specification of resources within the dataset, use the tool below to add them.",
  },
};

export const MODEL_RUN_UI_SCHEMA = {
  "ui:title": "Register a Model Run",
  start_time: {
    "ui:title": "Start time",
    "ui:description": "Specify the time when the model run started.",
    "ui:field": "unixTimestamp",
  },
  end_time: {
    "ui:title": "End time",
    "ui:description": "Specify the time when the model run completed.",
    "ui:field": "unixTimestamp",
  },
  display_name: {
    "ui:description": "Provide a short display name for this model run.",
  },
  description: {
    "ui:description": "Provide a description about this model run.",
  },
  model_version: {
    "ui:description":
      "Specify a version of the model used, if relevant. E.g. a commit hash, version identifier or other description.",
  },
  annotations: {
    "ui:title": "Model Run Annotations",
    "ui:description":
      "If your model run workflow template specified annotations (required and optional), you can provide values here. If you would not like to supply a value for an optional annotation, use the minus icon on the right to remove it.",
  },
  workflow_template_id: {
    "ui:title": "Workflow Template",
    "ui:description":
      "Select a registered workflow template from the search tool below.",
    "ui:field": "autoCompleteWorkflowTemplateLookup",
  },
  study_id: {
    "ui:title": "Study",
    "ui:description": "Select a registered study from the search tool below.",
    "ui:field": "autoCompleteStudyLookup",
  },
  inputs: {
    "ui:title": "Input Datasets",
    "ui:field": "fixedArray",
    "ui:description":
      "Provide an input dataset for each of the model run's templated inputs.",
    items: {
      ...DS_SPEC,
      dataset_template_id: {
        "ui:title": "Template",
        "ui:description": "Details of your selected input template.",
        "ui:field": "datasetTemplate",
      },
    },
  },
  outputs: {
    "ui:title": "Output Datasets",
    "ui:field": "fixedArray",
    "ui:description":
      "Provide an output dataset for each of the model run's templated outputs.",
    items: {
      ...DS_SPEC,
      dataset_template_id: {
        "ui:title": "Input Template",
        "ui:description": "Details of your selected input template.",
        "ui:field": "datasetTemplate",
      },
    },
  },
  associations: {
    "ui:title": "Associations",
    "ui:description":
      "A set of associations about people or organisations involved in this model run record.",
    modeller_id: {
      "ui:title": "Modeller",
      "ui:description":
        "Use the search tool below to select the Person who ran this model.",
      "ui:field": "autoCompletePersonLookup",
    },
    requesting_organisation_id: {
      "ui:title": "Organisation",
      "ui:description":
        "Use the search tool below to select the Organisation who is responsible for this model run.",
      "ui:field": "autoCompleteOrganisationLookup",
    },
  },
};

const customFields: { [name: string]: any } = {
  unixTimestamp: UnixTimestampField,
  autoCompleteDatasetTemplateLookup: AutoCompleteDatasetTemplateLookup,
  autoCompleteWorkflowTemplateLookup:
    AutoCompleteModelRunWorkflowDefinitionLookup,
  autoCompleteDatasetLookup: AutoCompleteDatasetLookup,
  autoCompleteStudyLookup: AutoCompleteStudyLookup,
  autoCompletePersonLookup: AutoCompletePersonLookup,
  autoCompleteOrganisationLookup: AutoCompleteOrganisationLookup,
  datasetTemplateMetadataOverride: DatasetTemplateAdditionalAnnotationsOverride,
  datasetTemplate: DatasetTemplateDisplay,
  fixedArray: ArrayField,
};

function ErrorListTemplate({ errors }: ErrorListProps) {
  const classes = useStyles();

  return (
    <Paper className={classes.errorListContainer} elevation={0}>
      <Typography variant="h6" className={classes.errorListTitle}>
        <ErrorOutlineIcon className={classes.errorIcon} />
        Your form has errors!
      </Typography>
      <Typography variant="subtitle1" className={classes.errorListSubtitle}>
        Your form could not be validated. The errors are listed below. Please
        scroll up and correct these errors before submitting the form.
      </Typography>
      <List className={classes.errorListList}>
        {errors.map((error, index) => (
          <ListItem key={index} className={classes.errorListItem}>
            <Stack
              direction="row"
              justifyItems={"flex-start"}
              spacing={2}
              alignItems="center"
            >
              <ErrorIcon color="action" />
              <Typography variant="body2" className={classes.errorText}>
                <b>{stylizeErrorProperty(error.property ?? "Form")}</b>
                <br />
                {error.message}
              </Typography>
            </Stack>
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}

export interface ModelRunFormProps {
  formData: {};
  setFormData: (formData: object) => void;
  onSubmit: () => void;
  submitEnabled: boolean;
  submitDisabledReason?: string;
  onCancel: () => void;
}
export const ModelRunForm = (props: ModelRunFormProps) => {
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
        schema={MODEL_RUN_JSON_SCHEMA as RJSFSchema}
        uiSchema={{
          ...MODEL_RUN_UI_SCHEMA,
          // Forces the form to always include the top level object
          disableOptional: true,
        }}
        fields={customFields}
        widgets={{}}
        formData={props.formData}
        validator={validator}
        onChange={(d) => {
          props.setFormData(d.formData);
        }}
        onSubmit={(form) => {
          props.onSubmit();
        }}
        showErrorList={"bottom"}
        templates={{ ErrorListTemplate }}
      >
        <Grid container item xs={12}>
          <Grid container item xs={12} className={classes.interactionContainer}>
            <Grid
              container
              item
              xs={12}
              className={classes.interactionPanel}
              direction="row"
            >
              <Button
                variant="outlined"
                className={classes.mainActionButton}
                onClick={props.onCancel}
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
                  <Alert variant="outlined" severity="warning">
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
