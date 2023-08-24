import { DATA_STORE_LINK, DOCUMENTATION_BASE_URL } from "react-libs";
import { ItemSubType } from "./shared-interfaces/RegistryModels";

export const nonEditEntityTypes: ItemSubType[] = ["DATASET", "MODEL_RUN"];

export const entityTypes: ItemSubType[] = [
    "DATASET",
    "DATASET_TEMPLATE",
    "MODEL",
    "MODEL_RUN",
    "MODEL_RUN_WORKFLOW_TEMPLATE",
    "ORGANISATION",
    "PERSON",
    "SOFTWARE",
    "WORKFLOW_TEMPLATE",
    "WORKFLOW_RUN",
    "CREATE",
    "VERSION",
];

export const filterableEntityTypes: ItemSubType[] = [
    "DATASET",
    "DATASET_TEMPLATE",
    "MODEL",
    "MODEL_RUN",
    "MODEL_RUN_WORKFLOW_TEMPLATE",
    "ORGANISATION",
    "PERSON",
    "CREATE",
    "VERSION",
];

export const searchableEntityTypes: ItemSubType[] = [
    "DATASET",
    "DATASET_TEMPLATE",
    "MODEL",
    "MODEL_RUN",
    "MODEL_RUN_WORKFLOW_TEMPLATE",
    "ORGANISATION",
    "PERSON",
    "CREATE",
    "VERSION",
];

export const registerableEntityTypes: ItemSubType[] = [
    "DATASET_TEMPLATE",
    "MODEL",
    "DATASET",
    "MODEL_RUN_WORKFLOW_TEMPLATE",
    "ORGANISATION",
    "PERSON",
];

export const entityRegisterDocumentationMap: Map<ItemSubType, string> = new Map(
    [
        [
            "DATASET_TEMPLATE",
            DOCUMENTATION_BASE_URL +
                "/information-system/provenance/registering-model-runs/model-workflow-configuration#dataset-template",
        ],
        [
            "MODEL",
            DOCUMENTATION_BASE_URL +
                "/information-system/provenance/registering-model-runs/establishing-required-entities.html#model",
        ],
        [
            "MODEL_RUN_WORKFLOW_TEMPLATE",
            DOCUMENTATION_BASE_URL +
                "information-system/provenance/registering-model-runs/model-workflow-configuration#model-run-workflow-template",
        ],
        [
            "ORGANISATION",
            DOCUMENTATION_BASE_URL +
                "/information-system/provenance/registering-model-runs/establishing-required-entities#organisation",
        ],
        [
            "PERSON",
            DOCUMENTATION_BASE_URL +
                "/information-system/provenance/registering-model-runs/establishing-required-entities#person",
        ],
    ]
);
