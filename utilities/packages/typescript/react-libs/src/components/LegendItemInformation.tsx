import { DOCUMENTATION_BASE_URL } from "../queries";
import { Swatches } from "../util";

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
            "/provenance/registering-model-runs/establishing-required-entities.html#person",
    },
    {
        colour: Swatches.organisationSwatch.colour,
        acronym: "O",
        name: "Organisation",
        href:
            DOCUMENTATION_BASE_URL +
            "/provenance/registering-model-runs/establishing-required-entities.html#organisation",
    },
    {
        colour: Swatches.datasetSwatch.colour,
        acronym: "D",
        name: "Dataset",
        href:
            DOCUMENTATION_BASE_URL +
            "/data-store/overview.html#data-store-overview",
    },
    {
        colour: Swatches.datasetTemplateSwatch.colour,
        acronym: "DT",
        name: "Dataset Template",
        href:
            DOCUMENTATION_BASE_URL +
            "/provenance/registering-model-runs/model-workflow-configuration.html#dataset-template",
    },
    {
        colour: Swatches.modelSwatch.colour,
        acronym: "M",
        name: "Model",
        href:
            DOCUMENTATION_BASE_URL +
            "/provenance/registering-model-runs/establishing-required-entities.html#model",
    },
    {
        colour: Swatches.modelRunSwatch.colour,
        acronym: "MR",
        name: "Model Run",
        href:
            DOCUMENTATION_BASE_URL +
            "/provenance/registering-model-runs/registration-process/overview.html#model-run-overview",
    },
    {
        colour: Swatches.modelRunWorkflowDefinitionSwatch.colour,
        acronym: "MRWT",
        name: "Model Run Workflow Template",
        href:
            DOCUMENTATION_BASE_URL +
            "/provenance/registering-model-runs/model-workflow-configuration.html#model-run-workflow-template",
    },
    {
        colour: Swatches.createSwatch.colour,
        acronym: "C",
        name: "Create",
        href:
            DOCUMENTATION_BASE_URL +
            "/registry/registering_and_updating.html#registering-an-entity",
    },
    {
        colour: Swatches.versionSwatch.colour,
        acronym: "V",
        name: "Version",
        href: DOCUMENTATION_BASE_URL + "/versioning/versioning-overview.html",
    },
    {
        colour: Swatches.studySwatch.colour,
        acronym: "S",
        name: "Study",
        href:
            DOCUMENTATION_BASE_URL +
            "/provenance/registering-model-runs/establishing-required-entities.html#study",
    },
];
