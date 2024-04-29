import { OptionallyRequiredCheck } from "../provena-interfaces/DataStoreAPI";
import { OptionallyRequiredConsentOverride } from "./OptionallyRequiredConsentOverride";
import { FieldProps } from "@rjsf/utils";

export const IndigenousKnowledgeOverride = (
  props: FieldProps<OptionallyRequiredCheck>,
) => {
  return (
    <OptionallyRequiredConsentOverride
      {...props}
      relevantLabel="Contains Indigenous Knowledge?"
      obtainedLabel="Necessary permission acquired?"
      // Customisation
      relevantErrorTitle={"Indigenous Knowledge unaccounted for"}
      relevantErrorContent={
        <p>
          You have marked the dataset as containing Indigenous Knowledge but
          have not obtained the necessary consents and permissions. This dataset
          cannot be uploaded to the Data Store.
        </p>
      }
      relevantSuccessTitle={"Indigenous Knowledge accounted for"}
      relevantSuccessContent={
        <p>
          You have marked the dataset as containing Indigenous Knowledge and
          have obtained the necessary consents and permissions. This dataset can
          be uploaded to the Data Store.
        </p>
      }
      // Edge case where irrelevant but obtained
      nonRelevantErrorTitle={"Indigenous Knowledge unnecessarily accounted for"}
      nonRelevantErrorContent={
        <p>
          You have marked the dataset as not containing Indigenous Knowledge but
          have noted that the necessary consents and permission have been
          granted. Please clarify whether Indigenous Knowledge is present.
        </p>
      }
      nonRelevantSuccessTitle={
        "Indigenous Knowledge is not present in this dataset"
      }
      nonRelevantSuccessContent={
        <p>
          You have marked the dataset as not containing Indigenous Knowledge.
          This dataset can be uploaded to the Data Store.
        </p>
      }
      descriptionContentOverride={
        <p>
          Does this dataset contain{" "}
          <a
            href="https://www.ipaustralia.gov.au/understanding-ip/indigenous-knowledge-ip"
            target="_blank"
            rel="noopener noreferrer"
          >
            Indigenous Knowledge
          </a>
          ? If so, do you have consent from the relevant Aboriginal and Torres
          Strait Islander communities for its use and access via this data
          store?
        </p>
      }
    />
  );
};

export const ExportControlsConsentOverride = (
  props: FieldProps<OptionallyRequiredCheck>,
) => {
  return (
    <OptionallyRequiredConsentOverride
      {...props}
      relevantLabel="Subject to export controls?"
      obtainedLabel="Cleared due diligence checks and obtained required permits?"
      // Customisation
      relevantErrorTitle={"Export controls unaccounted for"}
      relevantErrorContent={
        <p>
          You have marked the dataset as containing data subject to export
          controls but have not obtained the necessary due diligence checks and
          clearances. This dataset cannot be uploaded to the Data Store.
        </p>
      }
      relevantSuccessTitle={"Export controls accounted for"}
      relevantSuccessContent={
        <p>
          You have marked the dataset as containing data subject to export
          controls and have obtained the necessary due diligence checks and
          clearances. This dataset can be uploaded to the Data Store.
        </p>
      }
      // Edge case where irrelevant but obtained
      nonRelevantErrorTitle={"Export controls unnecessarily accounted for"}
      nonRelevantErrorContent={
        <p>
          You have marked the dataset as not containing data subject to export
          controls but have noted that the necessary due diligence checks and
          clearances have been obtained. Please clarify whether export sensitive
          data is present.
        </p>
      }
      nonRelevantSuccessTitle={"No export controlled data"}
      nonRelevantSuccessContent={
        <p>
          You have marked the dataset as not containing export sensitive data.
          This dataset can be uploaded to the Data Store.
        </p>
      }
    />
  );
};

export const DatasetEthicsRegistrationOverride = (
  props: FieldProps<OptionallyRequiredCheck>,
) => {
  return (
    <OptionallyRequiredConsentOverride
      {...props}
      relevantLabel="Subject to ethics and privacy concerns for registration?"
      obtainedLabel="Necessary consents and permissions acquired?"
      // Customisation
      relevantErrorTitle={"Ethics and privacy unaccounted for"}
      relevantErrorContent={
        <p>
          You have marked the dataset as containing data sensitive to ethics and
          privacy concerns but have not obtained the necessary consents and
          permissions. This dataset cannot be uploaded to the Data Store.
        </p>
      }
      relevantSuccessTitle={"Ethics and privacy accounted for"}
      relevantSuccessContent={
        <p>
          You have marked the dataset as containing data sensitive to ethics and
          privacy concerns and have obtained the necessary consents and
          permissions. This dataset can be uploaded to the Data Store.
        </p>
      }
      // Edge case where irrelevant but obtained
      nonRelevantErrorTitle={"Ethics and privacy unnecessarily accounted for"}
      nonRelevantErrorContent={
        <p>
          You have marked the dataset as not containing data sensitive to ethics
          and privacy concerns but have noted that the necessary consents and
          permission have been granted. Please clarify whether ethics and
          privacy sensitive data is present.
        </p>
      }
      nonRelevantSuccessTitle={
        "Dataset registration is not subject to ethics and privacy concerns"
      }
      nonRelevantSuccessContent={
        <p>
          You have marked the dataset as not containing any ethics or privacy
          sensitive data. This dataset can be uploaded to the Data Store.
        </p>
      }
    />
  );
};

export const DatasetEthicsAccessOverride = (
  props: FieldProps<OptionallyRequiredCheck>,
) => {
  return (
    <OptionallyRequiredConsentOverride
      {...props}
      relevantLabel="Subject to ethics and privacy concerns for data access?"
      obtainedLabel="Necessary consents and permissions acquired?"
      // Customisation
      relevantErrorTitle={"Ethics and privacy unaccounted for"}
      relevantErrorContent={
        <p>
          You have marked the dataset as containing data sensitive to ethics and
          privacy concerns but have not obtained the necessary consents and
          permissions. This dataset cannot be uploaded to the Data Store.
        </p>
      }
      relevantSuccessTitle={"Ethics and privacy accounted for"}
      relevantSuccessContent={
        <p>
          You have marked the dataset as containing data sensitive to ethics and
          privacy concerns and have obtained the necessary consents and
          permissions. This dataset can be uploaded to the Data Store.
        </p>
      }
      // Edge case where irrelevant but obtained
      nonRelevantErrorTitle={"Ethics and privacy unnecessarily accounted for"}
      nonRelevantErrorContent={
        <p>
          You have marked the dataset as not containing data sensitive to ethics
          and privacy concerns but have noted that the necessary consents and
          permission have been granted. Please clarify whether ethics and
          privacy sensitive data is present.
        </p>
      }
      nonRelevantSuccessTitle={
        "Dataset access is not subject to ethics and privacy concerns"
      }
      nonRelevantSuccessContent={
        <p>
          You have marked the dataset as not containing any ethics or privacy
          sensitive data. This dataset can be uploaded to the Data Store.
        </p>
      }
    />
  );
};
