import { DATA_STORE_LINK, DOCUMENTATION_BASE_URL } from "react-libs";
import { ItemSubType } from "./provena-interfaces/RegistryModels";

/** List of item subtypes that should not be edited from 
within the Registry UI. Either they should never be edited
(e.g., templates as this would break provenance) or they should
be edited from the Datastore UI (datasets)
*/
export const nonEditEntityTypes: ItemSubType[] = [
  "DATASET",
  "MODEL_RUN",
  "MODEL_RUN_WORKFLOW_TEMPLATE",
  "WORKFLOW_TEMPLATE",
  "DATASET_TEMPLATE"
];

/** List of item subtypes that should not be cloned from 
within the Registry UI. Either they should never be cloned,
or only cloned from Datastore UI.
*/
export const nonCloneEntityTypes: ItemSubType[] = [
  "DATASET",
  "MODEL_RUN",
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
