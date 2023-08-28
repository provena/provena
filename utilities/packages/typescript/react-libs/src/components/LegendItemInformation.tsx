import { Swatches } from "../util";
import { DOCUMENTATION_BASE_URL } from "../queries";

export interface LegendInformationProps {
    colour: string;
    acronym: string;
    href: string;
    name: string;
}

export const LegendInformation: readonly LegendInformationProps[] = [
    {
        colour: Swatches.personSwatch.colour,
        acronym: "P",
        name: "Person",
        href:
            DOCUMENTATION_BASE_URL +
            "/information-system/provenance/registering-model-runs/establishing-required-entities#person",
    },
    {
        colour: Swatches.organisationSwatch.colour,
        acronym: "O",
        name: "Organisation",
        href:
            DOCUMENTATION_BASE_URL +
            "/information-system/provenance/registering-model-runs/establishing-required-entities#organisation",
    },
    {
        colour: Swatches.datasetSwatch.colour,
        acronym: "D",
        name: "Dataset",
        href:
            DOCUMENTATION_BASE_URL +
            "/information-system/data-store/overview#data-store-overview",
    },
    {
        colour: Swatches.datasetTemplateSwatch.colour,
        acronym: "DT",
        name: "Dataset Template",
        href:
            DOCUMENTATION_BASE_URL +
            "/information-system/provenance/registering-model-runs/model-workflow-configuration.html#dataset-template",
    },
    {
        colour: Swatches.modelSwatch.colour,
        acronym: "M",
        name: "Model",
        href:
            DOCUMENTATION_BASE_URL +
            "/information-system/provenance/registering-model-runs/establishing-required-entities#model",
    },
    {
        colour: Swatches.modelRunSwatch.colour,
        acronym: "MR",
        name: "Model Run",
        href:
            DOCUMENTATION_BASE_URL +
            "/information-system/provenance/registering-model-runs/registration-process/overview.html#model-run-overview",
    },
    {
        colour: Swatches.modelRunWorkflowDefinitionSwatch.colour,
        acronym: "MRWT",
        name: "Model Run Workflow Template",
        href:
            DOCUMENTATION_BASE_URL +
            "/information-system/provenance/registering-model-runs/model-workflow-configuration#model-run-workflow-template",
    },
];
