import { entityRegisterDocumentationMap } from "../entityLists";
import { ItemSubType } from "../shared-interfaces/RegistryModels";

export const getRegisteringDocumentationLink = (
    currentSubtype: ItemSubType
): string | undefined => {
    // try getting the item from the documentation link map
    return entityRegisterDocumentationMap.get(currentSubtype);
};

export const registryVersionIdLinkResolver = (id: string): string => {
    // Help versioning items redirect to their tabs
    return `/item/${id}?view=versioning`;
};
