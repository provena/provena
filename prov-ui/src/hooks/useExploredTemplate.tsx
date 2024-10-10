import { useQuery } from "@tanstack/react-query";
import {
  DatasetType,
  ItemDatasetTemplate,
  ItemModelRunWorkflowTemplate,
} from "provena-interfaces/AuthAPI";
import {
  DatasetTemplateFetchResponse,
  ModelRunWorkflowTemplateFetchResponse,
} from "provena-interfaces/RegistryAPI";
import { fetchBySubtype } from "react-libs";

export interface PartialTemplatedDataset {
  dataset_template_id: string;
  dataset_type: DatasetType;
  resources?: {
    [k: string]: string;
  };
}

export interface ExploredTemplate {
  workflow_template_id: string;
  inputs: PartialTemplatedDataset[];
  outputs: PartialTemplatedDataset[];
  annotations?: {
    [k: string]: string;
  };
}

const fetchDatasetTemplate = async (
  id: string
): Promise<ItemDatasetTemplate> => {
  // fetch workflow template
  const templateResponse: DatasetTemplateFetchResponse = await fetchBySubtype(
    id,
    "DATASET_TEMPLATE",
    false
  );

  if (!templateResponse.status.success || !templateResponse.item) {
    throw new Error(
      `Failed to fetch dataset template with id: ${id}. Error message: ${
        templateResponse.status.details || "unknown."
      }`
    );
  }

  // Cast to non-seed since we don't allow it
  return templateResponse.item as ItemDatasetTemplate;
};

const buildExploredTemplate = (
  workflowTemplate: ItemModelRunWorkflowTemplate,
  inputTemplates: ItemDatasetTemplate[],
  outputTemplates: ItemDatasetTemplate[]
): ExploredTemplate => {
  // Build the template progressively
  var buildingTemplate: Partial<ExploredTemplate> = {};

  // Set the input template id
  buildingTemplate.workflow_template_id = workflowTemplate.id;

  // Check for annotations
  buildingTemplate.annotations = {};

  // required
  for (const ann of workflowTemplate.annotations?.required ?? []) {
    buildingTemplate.annotations[ann] = "TODO";
  }

  // optional
  for (const ann of workflowTemplate.annotations?.optional ?? []) {
    buildingTemplate.annotations[ann] = "Optional TODO";
  }

  // Now fill in each input/output template
  buildingTemplate.inputs = [];
  buildingTemplate.outputs = [];

  const buildTemplates = (templates: ItemDatasetTemplate[]) => {
    const outputs = [];
    for (const template of templates) {
      // Start up with empty resources
      var resources: { [k: string]: string } = {};

      // find the deferred resources
      const deferred = template.deferred_resources ?? [];

      // Build out resources - TODO key for each deferred
      // TODO handle optional
      for (const def of deferred) {
        resources[def.key] = "TODO";
      }

      outputs.push({
        dataset_template_id: template.id,
        dataset_type: "DATA_STORE",
        resources,
      } satisfies PartialTemplatedDataset);
    }
    return outputs;
  };

  buildingTemplate.inputs = buildTemplates(inputTemplates);
  buildingTemplate.outputs = buildTemplates(outputTemplates);

  // return the completed template
  return buildingTemplate as ExploredTemplate;
};

export interface UseExploredTemplateProps {
  workflowTemplateId?: string;
}
export const useExploredTemplate = (props: UseExploredTemplateProps) => {
  /**
    Hook: useExploredTemplate
    
    */

  // unpack props
  const { workflowTemplateId } = props;

  // run various queries
  const query = useQuery({
    queryKey: ["detailed explore", workflowTemplateId],
    enabled: !!workflowTemplateId,
    queryFn: async () => {
      // fetch workflow template
      const templateResponse: ModelRunWorkflowTemplateFetchResponse =
        await fetchBySubtype(
          workflowTemplateId!,
          "MODEL_RUN_WORKFLOW_TEMPLATE",
          false
        );

      if (!templateResponse.status.success || !templateResponse.item) {
        throw new Error(
          `Failed to fetch workflow template with id: ${workflowTemplateId}. Error message: ${
            templateResponse.status.details || "unknown."
          }`
        );
      }

      // Cast to non-seed since we don't allow it
      const workflowTemplate =
        templateResponse.item as ItemModelRunWorkflowTemplate;

      // TODO consider optional templates
      const inputTemplateIds = (workflowTemplate.input_templates ?? []).map(
        (t) => {
          return t.template_id;
        }
      );

      const outputTemplateIds = (workflowTemplate.output_templates ?? []).map(
        (t) => {
          return t.template_id;
        }
      );

      const inputTemplatesPromises = inputTemplateIds.map(fetchDatasetTemplate);
      const outputTemplatesPromises =
        outputTemplateIds.map(fetchDatasetTemplate);

      const [inputDatasetTemplates, outputDatasetTemplates] = await Promise.all(
        [
          Promise.all(inputTemplatesPromises),
          Promise.all(outputTemplatesPromises),
        ]
      );

      return {
        prefill: buildExploredTemplate(
          workflowTemplate,
          inputDatasetTemplates,
          outputDatasetTemplates
        ),
        workflowTemplate,
        inputDatasetTemplates,
        outputDatasetTemplates,
      };
    },
  });

  return { query };
};
