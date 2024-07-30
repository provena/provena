import { OptionallyRequiredDate } from "react-libs/provena-interfaces/RegistryModels";
import { OptionallyRequiredCheck } from "../provena-interfaces/DataStoreAPI";
import { OptionallyRequiredConsentOverride } from "./OptionallyRequiredConsentOverride";
import { FieldProps } from "@rjsf/utils";
import { OptionallyRequiredDateOverride } from "./OptionallyRequiredDatasetDateOverride";

export const PublishedDateOverride = (
  props: FieldProps<OptionallyRequiredDate>
) => {
  return (
    <OptionallyRequiredDateOverride
      {...props}
      relevantLabel="Dataset has been published?"
      dateLabel="Dataset publication date"
      // Customisation
      relevantErrorTitle={"Please provide publication date"}
      relevantErrorContent={
        <p>
          You have marked the dataset as being published but
          have not provided a publication date yet. This dataset
          cannot be created in the Data Store.
        </p>
      }
      relevantSuccessTitle={"Dataset has been published"}
      relevantSuccessContent={
        <p>
          You have marked the dataset as being published and have provided the publication date. This dataset can be created in the Data Store.
        </p>
      }
      // Edge case where irrelevant but obtained
      nonRelevantErrorTitle={"Dataset not yet published"}
      nonRelevantErrorContent={
        <p>
          You have marked the dataset as not yet published. You can still register the metadata record and update this field later when the dataset is published.
        </p>
      }
      nonRelevantSuccessTitle={
        "Dataset has not been published"
      }
      nonRelevantSuccessContent={
        <p>
          You have marked the dataset as not being published. This dataset can be created in the Data Store.
        </p>
      }
      descriptionContentOverride={
        <p>
          Has the data associated with this metadata record been published yet?
        </p>
      }
    />
  );
};

export const CreatedDateOverride = (
  props: FieldProps<OptionallyRequiredDate>
) => {
  return (                  
    <OptionallyRequiredDateOverride
      {...props}
      relevantLabel="Dataset has been created?"
      dateLabel="Dataset creation date"
      // Customisation
      relevantErrorTitle={"Please provide dataset creation date"}
      relevantErrorContent={
        <p>
          You have marked the dataset record's data as being created but
          have not provided a creation date yet. This dataset record
          cannot be created in the Data Store.
        </p>
      }
      relevantSuccessTitle={"Dataset has been created"}
      relevantSuccessContent={
        <p>
          You have marked the dataset associated with this record as being created and have provided the creation date. This dataset record can be created in the Data Store.
        </p>
      }
      // Edge case where irrelevant but obtained
      nonRelevantErrorTitle={"Dataset not yet created"}
      nonRelevantErrorContent={
        <p>
          You have marked the dataset as not yet created. You can still register the metadata record and update this field later when the data is created.
        </p>
      }
      nonRelevantSuccessTitle={
        "Dataset has not been created"
      }
      nonRelevantSuccessContent={
        <p>
          You have marked the dataset as not being created. This dataset record can be created in the Data Store.
        </p>
      }
      descriptionContentOverride={
        <p>
          Has the data associated with this metadata record been created yet?
        </p>
      }
    />
  );
};
