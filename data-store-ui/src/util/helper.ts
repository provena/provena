export const datasetVersionIdLinkResolver = (id: string): string => {
    // Help versioning items redirect to their tabs
    return `/dataset/${id}?view=versioning`;
};
