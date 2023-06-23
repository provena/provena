import { AutoCompleteOrganisationLookup } from "react-libs";
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
    associations: {
        organisation_id: {
            "ui:field": "searchOrganisation",
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
    ethicsAccess: DatasetEthicsAccessOverride,
    ethicsRegistration: DatasetEthicsRegistrationOverride,
    autoCompleteLicense: AutoCompleteLicense,
    accessInfoOverride: AccessInfoOverride,
    indigenousKnowledge: IndigenousKnowledgeOverride,
    exportControls: ExportControlsConsentOverride,
    preferredCitation: PreferredCitationOverride,
};