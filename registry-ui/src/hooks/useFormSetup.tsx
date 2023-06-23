import { useEffect } from "react";
import {
    BaseLoadedEntity,
    LoadedEntity,
    combineLoadStates,
    mapQueryToLoadedEntity,
    useTypedLoadedItem,
    useUntypedLoadedItem,
} from "react-libs";
import { ItemBase, ItemSubType } from "../shared-interfaces/RegistryModels";
import { useSchemas } from "./useSchemas";

export interface UseFormSetupProps {
    // Enabled - central control over whether fetching should occur
    enabled?: boolean;

    // Are we editing? False = create
    editing: boolean;

    // Specify the ID if editing
    id?: string;

    // Subtype - if not known then ID must be supplied
    subtype?: ItemSubType;

    // Add an event for when the data is loaded from existing entity
    onExistingEntityLoaded?: (item: ItemBase) => void;
}

export interface UseFormSetupOutput extends BaseLoadedEntity {
    // Loaded schemas
    jsonSchema?: LoadedEntity<any>;
    uiSchema?: LoadedEntity<any>;

    // Only supplied when editing
    existingItem?: LoadedEntity<ItemBase | undefined>;

    // Returns the subtype - if editing this is dynamically resolved from the
    // item fetch - if provided, returns the same
    subtype?: ItemSubType;
}
export const useFormSetup = (props: UseFormSetupProps): UseFormSetupOutput => {
    /**
    Hook: useFormSetup

    Manages the setup of all required components for creating/editing items with a form.
    */

    const fetchingEnabled = props.enabled !== undefined ? props.enabled : true;

    // Untyped item if editing and subtype unknown
    const loadedUntypedItem = useUntypedLoadedItem({
        id: props.id,
        enabled: fetchingEnabled && props.subtype === undefined,
    });

    // Derive subtype as either props provided or through loaded item
    const subtype = props.subtype || loadedUntypedItem.data?.item_subtype;

    // Load item if editing
    const loadedTypedItem = useTypedLoadedItem({
        id: props.id,
        subtype: subtype,
        enabled: fetchingEnabled && props.editing && subtype !== undefined,
    });

    const loadedItemLoadState: LoadedEntity<ItemBase | undefined> | undefined =
        props.editing
            ? {
                  ...loadedTypedItem,
                  data: loadedTypedItem.item,
              }
            : undefined;

    // Setup event listener for when data changes
    useEffect(() => {
        const data = loadedItemLoadState?.data;
        if (data !== undefined) {
            // Conditionally execute the data change when loaded successfully
            props.onExistingEntityLoaded && props.onExistingEntityLoaded(data);
        }
    }, [loadedItemLoadState?.data]);

    // Load the item schema and ui schema using a custom hook
    const schemas = useSchemas({ subtype: subtype, enabled: fetchingEnabled });

    // Combined state
    var states: Array<BaseLoadedEntity> = [schemas, loadedUntypedItem];
    if (loadedItemLoadState) {
        states.push(loadedItemLoadState);
    }
    const combined = combineLoadStates(states);

    // Return all results
    return {
        existingItem: loadedItemLoadState,
        jsonSchema: schemas.jsonSchema,
        uiSchema: schemas.uiSchema,
        subtype,
        ...combined,
    };
};
