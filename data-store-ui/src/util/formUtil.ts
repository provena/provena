import {
  AutoCompleteOrganisationLookup,
  AutoCompletePersonLookup,
} from "react-libs";
import AccessInfoOverride from "../components/AccessInfoOverride";
import AutoCompleteLicense from "../components/AutoCompleteLicense";
import {
  DatasetEthicsAccessOverride,
  DatasetEthicsRegistrationOverride,
  ExportControlsConsentOverride,
  IndigenousKnowledgeOverride,
} from "../components/OptionallyRequiredConsents";
import { PreferredCitationOverride } from "../components/PreferredCitationOverride";

export const uiSchema = {
  // This is used in the optional field override to disable the optional
  // switch at top level
  disableOptional: true,
  associations: {
    organisation_id: {
      "ui:field": "searchOrganisation",
    },
    data_custodian_id: {
      "ui:field": "searchPerson",
    },
  },
  approvals: {
    ethics_registration: {
      "ui:field": "ethicsRegistration",
    },
    ethics_access: {
      "ui:field": "ethicsAccess",
    },
    indigenous_knowledge: {
      "ui:field": "indigenousKnowledge",
    },
    export_controls: {
      "ui:field": "exportControls",
    },
  },
  dataset_info: {
    publisher_id: {
      "ui:field": "searchOrganisation",
    },
    license: {
      "ui:field": "autoCompleteLicense",
    },
    description: {
      "ui:widget": "textarea",
    },
    access_info: {
      "ui:field": "accessInfoOverride",
    },
    preferred_citation: {
      "ui:field": "preferredCitation",
    },
  },
};
export const fields: { [name: string]: any } = {
  searchOrganisation: AutoCompleteOrganisationLookup,
  searchPerson: AutoCompletePersonLookup,
  ethicsAccess: DatasetEthicsAccessOverride,
  ethicsRegistration: DatasetEthicsRegistrationOverride,
  autoCompleteLicense: AutoCompleteLicense,
  accessInfoOverride: AccessInfoOverride,
  indigenousKnowledge: IndigenousKnowledgeOverride,
  exportControls: ExportControlsConsentOverride,
  preferredCitation: PreferredCitationOverride,
};
