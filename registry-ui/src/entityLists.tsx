import { DATA_STORE_LINK, DOCUMENTATION_BASE_URL } from "react-libs";
import { ItemSubType } from "./provena-interfaces/RegistryModels";

export const nonEditEntityTypes: ItemSubType[] = [
  "DATASET",
  "MODEL_RUN",
  "MODEL_RUN_WORKFLOW_TEMPLATE",
  "WORKFLOW_TEMPLATE",
  "DATASET_TEMPLATE"
];

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
  "STUDY",
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
  "STUDY",
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
  "STUDY",
];

export const registerableEntityTypes: ItemSubType[] = [
  "DATASET_TEMPLATE",
  "MODEL",
  "DATASET",
  "MODEL_RUN_WORKFLOW_TEMPLATE",
  "ORGANISATION",
  "PERSON",
  "STUDY",
];

export const entityRegisterDocumentationMap: Map<ItemSubType, string> = new Map(
  [
    [
      "DATASET_TEMPLATE",
      DOCUMENTATION_BASE_URL +
        "/provenance/registering-model-runs/model-workflow-configuration.html#dataset-template",
    ],
    [
      "MODEL",
      DOCUMENTATION_BASE_URL +
        "/provenance/registering-model-runs/establishing-required-entities.html#model",
    ],
    [
      "MODEL_RUN_WORKFLOW_TEMPLATE",
      DOCUMENTATION_BASE_URL +
        "/provenance/registering-model-runs/model-workflow-configuration.html#model-run-workflow-template",
    ],
    [
      "ORGANISATION",
      DOCUMENTATION_BASE_URL +
        "/provenance/registering-model-runs/establishing-required-entities.html#organisation",
    ],
    [
      "PERSON",
      DOCUMENTATION_BASE_URL +
        "/provenance/registering-model-runs/establishing-required-entities.html#person",
    ],
    [
      "STUDY",
      DOCUMENTATION_BASE_URL +
        "/provenance/registering-model-runs/establishing-required-entities.html#study",
    ],
  ],
);
