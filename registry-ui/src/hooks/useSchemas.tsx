import { useQuery } from "@tanstack/react-query";
import {
  BaseLoadedEntity,
  LoadedEntity,
  combineLoadStates,
  getJsonSchema,
  getUiSchema,
  mapQueryToLoadedEntity,
} from "react-libs";
import { ItemSubType } from "../provena-interfaces/RegistryModels";

export interface UseSchemasProps {
  subtype?: ItemSubType;
  enabled?: boolean;
}

export interface UseSchemasOutput extends BaseLoadedEntity {
  uiSchema?: LoadedEntity<any>;
  jsonSchema?: LoadedEntity<any>;
}
export const useSchemas = (props: UseSchemasProps): UseSchemasOutput => {
  /**
    Hook: useSchemas
    

    Manages the UI and JSON schemas for an item specified by subtype.

    Is disabled if subtype is unsupplied.
    */

  const fetchingEnabled = props.enabled !== undefined ? props.enabled : true;

  // 1 minute cache time
  const cacheTime = 60000;
  const uiFetch = useQuery({
    queryKey: ["uischema", props.subtype ?? "unknown"],
    queryFn: () => {
      return getUiSchema(props.subtype!);
    },
    staleTime: cacheTime,
    enabled: fetchingEnabled && props.subtype !== undefined,
  });
  const jsonFetch = useQuery({
    queryKey: ["jsonschema", props.subtype ?? "unknown"],
    queryFn: () => {
      return getJsonSchema(props.subtype!);
    },
    staleTime: cacheTime,
    enabled: fetchingEnabled && props.subtype !== undefined,
  });

  // Derive load states
  const uiSchema = {
    data: uiFetch.data?.ui_schema,
    ...mapQueryToLoadedEntity(uiFetch),
  };
  const jsonSchema = {
    data: jsonFetch.data?.json_schema,
    ...mapQueryToLoadedEntity(uiFetch),
  };

  // And combine
  const combined = combineLoadStates([uiSchema, jsonSchema]);

  return {
    uiSchema: props.subtype ? uiSchema : undefined,
    jsonSchema: props.subtype ? jsonSchema : undefined,
    ...combined,
  };
};
