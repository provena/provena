import { FieldProps } from "@rjsf/utils";
import { SubtypeSearchAutoComplete } from "./SubtypeSearchOrManualFormOverride";

type FormProps = FieldProps<string | undefined>;

export const AutoCompleteModelLookup = (props: FormProps) => {
  return <SubtypeSearchAutoComplete {...props} subtype={"MODEL"} />;
};

interface AutoCompleteOrganisationPropType
  extends FieldProps<string | undefined> {}

export const AutoCompleteOrganisationLookup = (
  props: AutoCompleteOrganisationPropType
) => {
  return <SubtypeSearchAutoComplete {...props} subtype={"ORGANISATION"} />;
};

interface AutoCompleteDatasetTemplatePropType
  extends FieldProps<string | undefined> {}

export const AutoCompleteDatasetTemplateLookup = (
  props: AutoCompleteDatasetTemplatePropType
) => {
  return <SubtypeSearchAutoComplete {...props} subtype={"DATASET_TEMPLATE"} />;
};

interface AutoCompleteDatasetPropType extends FieldProps<string | undefined> {}

export const AutoCompleteDatasetLookup = (
  props: AutoCompleteDatasetPropType
) => {
  return <SubtypeSearchAutoComplete {...props} subtype={"DATASET"} />;
};

interface AutoCompleteStudyPropType extends FieldProps<string | undefined> {}

export const AutoCompleteStudyLookup = (props: AutoCompleteStudyPropType) => {
  return <SubtypeSearchAutoComplete {...props} subtype={"STUDY"} />;
};

interface AutoCompletePersonPropType extends FieldProps<string | undefined> {}

export const AutoCompletePersonLookup = (props: AutoCompletePersonPropType) => {
  return <SubtypeSearchAutoComplete {...props} subtype={"PERSON"} />;
};

interface AutoCompleteModelRunWorkflowDefinitionPropType
  extends FieldProps<string | undefined> {}

export const AutoCompleteModelRunWorkflowDefinitionLookup = (
  props: AutoCompleteModelRunWorkflowDefinitionPropType
) => {
  return (
    <SubtypeSearchAutoComplete
      {...props}
      subtype={"MODEL_RUN_WORKFLOW_TEMPLATE"}
    />
  );
};
