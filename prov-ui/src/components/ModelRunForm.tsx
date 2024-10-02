import { Alert, Button, Grid } from "@mui/material";
import { Theme } from "@mui/material/styles";
import createStyles from "@mui/styles/createStyles";
import makeStyles from "@mui/styles/makeStyles";
import { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import {
  AutoCompleteDatasetLookup,
  AutoCompleteDatasetTemplateLookup,
  AutoCompleteModelRunWorkflowDefinitionLookup,
  AutoCompleteOrganisationLookup,
  AutoCompletePersonLookup,
  AutoCompleteStudyLookup,
  DatasetTemplateAdditionalAnnotationsOverride,
  Form,
  UnixTimestampField,
} from "react-libs";

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
  })
);

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
          additionalProperties: { type: "string" },
        },
      },
      required: ["dataset_template_id", "dataset_id", "dataset_type"],
    },
  },
  properties: {
    workflow_template_id: { type: "string" },
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
      additionalProperties: { type: "string" },
    },
  },
  required: [
    "workflow_template_id",
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
  "ui:title": "Input Dataset Information",
  dataset_template_id: {
    "ui:title": "Dataset Template",
    "ui:description":
      "Use the search tool below to select the registered dataset template from the workflow template.",
    "ui:field": "autoCompleteDatasetTemplateLookup",
  },
  dataset_id: {
    "ui:title": "Dataset",
    "ui:description":
      "Use the search tool below to select the dataset which satisfies this template.",
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
      "If your model run workflow template specified annotations (required or optional), you can provide values here.",
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
    "ui:description":
      "Provide an input dataset for each of the model run's templated inputs.",
    items: DS_SPEC,
  },
  outputs: {
    "ui:title": "Output Datasets",
    "ui:description":
      "Provide an output dataset for each of the model run's templated outputs.",
    items: DS_SPEC,
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
};

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
